from typing import Any, Generator, override

from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager, ThrottledTimer, Utils
from Py4GWCoreLib.Overlay import Overlay
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Widgets.CustomBehaviors.primitives.parties.party_flagging_manager import PartyFlaggingManager
from Widgets.CustomBehaviors.primitives.scores.comon_score import CommonScore
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology
from Widgets.CustomBehaviors.primitives.bus.event_bus import EventBus

class FollowFlagUtilityNew(CustomSkillUtilityBase):
    """
    Utility that follows assigned flag positions from shared memory.

    Uses PartyFlaggingManager to access flag assignments:
    - Each player is assigned to a flag index (0-10)
    - Flag positions are stored in shared memory
    - Players move to their assigned flag position
    """

    def __init__(
            self,
            event_bus: EventBus,
            current_build: list[CustomSkill],
            allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("follow_flag_new"),
            in_game_build=current_build,
            score_definition=ScoreStaticDefinition(CommonScore.FOLLOW_FLAG.value),
            allowed_states=allowed_states,
            utility_skill_typology=UtilitySkillTypology.FOLLOWING)

        self.score_definition: ScoreStaticDefinition = ScoreStaticDefinition(CommonScore.FOLLOW_FLAG.value)
        self.throttle_timer = ThrottledTimer(1000)

        # Use singleton manager for all configuration
        self.manager =  CustomBehaviorParty().party_flagging_manager
        
    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if current_state is BehaviorState.IDLE: return False
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        if GLOBAL_CACHE.Party.IsPartyLeader(): return False
        return True

    def _get_my_assigned_flag_position(self) -> tuple[float, float] | None:
        """Get the flag position assigned to this player from shared memory"""
        try:
            # Use account email as stable identifier (agent ID changes across maps)
            my_email = GLOBAL_CACHE.Player.GetAccountEmail()
            if not my_email:
                return None

            # Find which flag index is assigned to me
            flag_index = self.manager.get_my_flag_index(my_email)
            if flag_index is None:
                return None

            # Get the position for that flag
            x, y = self.manager.get_flag_position(flag_index)

            # Check if position is valid (not 0, 0)
            if x == 0.0 and y == 0.0:
                return None

            return (x, y)
        except Exception as e:
            print(f"FollowFlagUtilityNew._get_my_assigned_flag_position error: {e}")
            return None

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        if self.allowed_states is not None and current_state not in self.allowed_states:
            return None

        # Get my assigned flag position from shared memory
        flag_pos = self._get_my_assigned_flag_position()
        if flag_pos is None:
            return None

        my_pos = GLOBAL_CACHE.Player.GetXY()
        if my_pos is None:
            return None

        # Calculate distance from assigned flag
        distance_from_flag = Utils.Distance(flag_pos, my_pos)

        # Use movement threshold from manager
        movement_threshold = self.manager.movement_threshold

        # If very close to flag, don't move
        if distance_from_flag < 10:
            return None

        # If far from flag, high priority
        if distance_from_flag > movement_threshold * 2:
            return CommonScore.FOLLOW_FLAG_REQUIRED.value

        # If outside threshold, normal priority
        if distance_from_flag > movement_threshold:
            return CommonScore.FOLLOW_FLAG.value

        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        if not self.throttle_timer.IsExpired():
            yield
            return BehaviorResult.ACTION_SKIPPED

        # Get my assigned flag position from shared memory
        flag_pos = self._get_my_assigned_flag_position()
        if flag_pos is None:
            yield
            return BehaviorResult.ACTION_SKIPPED

        # Move to assigned flag position
        ActionQueueManager().ResetQueue("ACTION")
        GLOBAL_CACHE.Player.Move(flag_pos[0], flag_pos[1])
        self.throttle_timer.Reset()

        yield from custom_behavior_helpers.Helpers.wait_for(1000)
        return BehaviorResult.ACTION_PERFORMED

    def draw_overlay(self, current_state: BehaviorState) -> None:
        """
        Draw debug overlay showing all flag positions as circles.
        This is the public method to be called from GUI.
        """
        # Only draw if enabled
        if not self.manager.enable_debug_overlay:
            return

        try:
            # Get my position for Z coordinate
            my_pos = GLOBAL_CACHE.Player.GetXY()
            if my_pos is None or len(my_pos) != 2:
                return

            my_agent_id = GLOBAL_CACHE.Player.GetAgentID()
            if my_agent_id is None:
                return

            _, _, my_z = GLOBAL_CACHE.Agent.GetXYZ(my_agent_id)

            # Get my account email to highlight my assigned flag
            my_email = GLOBAL_CACHE.Player.GetAccountEmail()
            if not my_email:
                return

            Overlay().BeginDraw()

            # Draw all 12 flag positions
            for flag_index in range(12):
                account_email, flag_x, flag_y = self.manager.get_flag_data(flag_index)

                # Skip unassigned flags (email == "") or invalid positions
                if not account_email or (flag_x == 0.0 and flag_y == 0.0):
                    continue

                # Determine color based on whether this is my flag
                if account_email == my_email:
                    # My flag - bright green
                    circle_color = Utils.RGBToColor(0, 255, 0, 200)
                    fill_color = Utils.RGBToColor(0, 255, 0, 100)
                    text_color = Utils.RGBToColor(0, 255, 0, 255)
                else:
                    # Other player's flag - cyan
                    circle_color = Utils.RGBToColor(0, 200, 255, 200)
                    fill_color = Utils.RGBToColor(0, 200, 255, 80)
                    text_color = Utils.RGBToColor(0, 200, 255, 255)

                # Draw filled circle for flag position
                Overlay().DrawPolyFilled3D(flag_x, flag_y, my_z, 25,
                                          fill_color, numsegments=16)

                # Draw circle outline
                Overlay().DrawPoly3D(flag_x, flag_y, my_z, 25,
                                    circle_color, numsegments=16, thickness=3.0)

                # Draw flag number
                Overlay().DrawText3D(flag_x, flag_y, my_z - 100,
                                   f"Flag {flag_index + 1}",
                                   text_color,
                                   autoZ=False, centered=True, scale=1.0)

                # If this is my flag, draw a line from me to it
                if account_email == my_email:
                    Overlay().DrawLine3D(my_pos[0], my_pos[1], my_z,
                                        flag_x, flag_y, my_z,
                                        Utils.RGBToColor(0, 255, 0, 150), thickness=2.0)

                    # Draw distance to my flag
                    distance = Utils.Distance(my_pos, (flag_x, flag_y))
                    mid_x = (my_pos[0] + flag_x) / 2
                    mid_y = (my_pos[1] + flag_y) / 2
                    Overlay().DrawText3D(mid_x, mid_y, my_z - 25,
                                       f"{distance:.0f}",
                                       Utils.RGBToColor(0, 255, 0, 255),
                                       autoZ=False, centered=True, scale=1.0)

            # Draw my position (blue circle)
            Overlay().DrawPoly3D(my_pos[0], my_pos[1], my_z, 25,
                                Utils.RGBToColor(0, 100, 255, 200), numsegments=16, thickness=3.0)

        except Exception as e:
            # Silently fail on debug UI errors
            print(f"FollowFlagUtilityNew.draw_overlay error: {e}")
            raise e
        finally:
            Overlay().EndDraw()