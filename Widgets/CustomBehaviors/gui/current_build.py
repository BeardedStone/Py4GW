import os
import pathlib
import re
import sys
from Py4GWCoreLib import IconsFontAwesome5, ImGui, Player, PyImGui
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Py4GWcorelib import Color, Utils
from Widgets.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Widgets.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import CustomBehaviorWidgetMemoryManager
from Widgets.CustomBehaviors.primitives.skills.bonds.per_type.custom_buff_target import BuffConfigurationPerProfession
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.primitives import constants
from Widgets.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology
from Widgets.CustomBehaviors.primitives.skills.utility_skill_typology_color import UtilitySkillTypologyColor

shared_data = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
script_directory = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_directory, os.pardir))
py4gw_root_directory = project_root + f"\\..\\..\\"
WITH_DETAIL = False
EXPANDED_SKILL_IDS: set[str] = set()




@staticmethod
def render():
    global WITH_DETAIL

    current_build:CustomBehaviorBaseUtility | None = CustomBehaviorLoader().custom_combat_behavior
    if current_build is None:
        PyImGui.text(f"Current build is None.")
        if PyImGui.button(f"{IconsFontAwesome5.ICON_SYNC} Search build again"):
            CustomBehaviorLoader().refresh_custom_behavior_candidate()
        return

    if constants.DEBUG:
        # PyImGui.same_line(0, 10)
        PyImGui.text(f"HasLoaded : {CustomBehaviorLoader()._has_loaded}")
        # PyImGui.same_line(0, 10)
        if CustomBehaviorLoader().custom_combat_behavior is not None:
            PyImGui.text(f"IsExecutingUtilitySkills:{CustomBehaviorLoader().custom_combat_behavior.is_executing_utility_skills()}")
        pass

    if CustomBehaviorLoader().custom_combat_behavior is not None:
        PyImGui.text(f"Selected template : {CustomBehaviorLoader().custom_combat_behavior.__class__.__name__}")
        PyImGui.text(f"Player state:{CustomBehaviorLoader().custom_combat_behavior.get_state()}")
        PyImGui.text(f"Final state (with party override):{CustomBehaviorLoader().custom_combat_behavior.get_final_state()}")

    if CustomBehaviorLoader().custom_combat_behavior.get_is_enabled():
        if PyImGui.button(f"{IconsFontAwesome5.ICON_TIMES} Disable ALL"):
            CustomBehaviorLoader().custom_combat_behavior.disable()
    else:
        if PyImGui.button(f"{IconsFontAwesome5.ICON_CHECK} Enable ALL"):
            CustomBehaviorLoader().custom_combat_behavior.enable()
    pass

    PyImGui.same_line(0, 5)
    PyImGui.same_line(0, -1)
    WITH_DETAIL = PyImGui.checkbox("with detailled informations", WITH_DETAIL)

    # if current_build is not None and type(current_build).mro()[1].__name__ != CustomBehaviorBaseUtility.__name__:
    #     PyImGui.separator()
    #     PyImGui.text(f"Generic skills : ")
    #     generic_behavior_build:list[CustomSkill] = current_build.get_generic_behavior_build()
    #     if generic_behavior_build is not None:
    #         for skill in generic_behavior_build:
    #             PyImGui.text(f"bbb {skill.skill_name}")

    # print(type(current_build))
    # print(CustomBehaviorBaseUtility)
    # print(type(current_build).mro()[1].__name__)  # Should be CustomBehaviorBaseUtility
    # print(id(CustomBehaviorBaseUtility))
    # print('CustomBehaviorBaseUtility' in type(current_build).mro()[0].__name__)
    # and isinstance(current_build, CustomBehaviorBaseUtility)
    # print(type(current_build).mro()[1].__name__ == CustomBehaviorBaseUtility.__name__)

    if current_build is not None and type(current_build).mro()[1].__name__ == CustomBehaviorBaseUtility.__name__:
        PyImGui.separator()
        # PyImGui.text(f"Generic skills - Utility system : ")
        instance: CustomBehaviorBaseUtility = current_build
        # utilities: list[CustomSkillUtilityBase] = instance.get_skills_final_list()

        # for utility in utilities:
        #     PyImGui.text(f"{utility.custom_skill.skill_name} {utility.additive_score_weight}")



        # Two side-by-side child containers with vertical scrollbars
        # Precompute scores once for both panels
        scores: list[tuple[CustomSkillUtilityBase, float | None]] = instance.get_all_scores()

        # Unified panel with tabs for skill detail and scoring
        if PyImGui.begin_child("skills_panel", size=(500, 600), border=True, flags=PyImGui.WindowFlags.NoFlag):
            if PyImGui.begin_tab_bar("skills_tabs"):
                # Tab 1: Skill Detail (per typology)
                if PyImGui.begin_tab_item("skill detail"):
                    PyImGui.text("allow you to deep dive configuration of skills")
                    scores_by_typology = sorted(scores, key=lambda s: (s[0].utility_skill_typology.value, s[0].custom_skill.skill_name))
                    if PyImGui.begin_table("skills_detailed", 2, int(PyImGui.TableFlags.SizingStretchProp)):
                        PyImGui.table_setup_column("A")
                        PyImGui.table_setup_column("B")
                        # PyImGui.table_headers_row()
                        for score in scores_by_typology:
                            def label_generic_utility(utility: CustomSkillUtilityBase) -> str:
                                if utility.__class__.__name__ == "HeroAiUtility":
                                    return f"HeroAI: "
                                return ""
                            score_text = f"{score[1]:06.4f}" if score[1] is not None else "Ø"
                            texture_file = score[0].custom_skill.get_texture(py4gw_root_directory, project_root)

                            PyImGui.table_next_row()
                            PyImGui.table_next_column()
                            color = UtilitySkillTypologyColor.get_color_from_typology(score[0].utility_skill_typology)
                            if score[0].is_enabled and CustomBehaviorParty().get_typology_is_enabled(score[0].utility_skill_typology) and instance.get_final_is_enabled():
                                PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
                                PyImGui.push_style_color(PyImGui.ImGuiCol.Border, color)
                                if ImGui.ImageButton(f"{score[0].custom_skill.skill_name}", texture_file, 35, 35):
                                    score[0].is_enabled = False
                                PyImGui.pop_style_var(1)
                                PyImGui.pop_style_color(1)
                            else:
                                PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
                                PyImGui.push_style_color(PyImGui.ImGuiCol.Border, Utils.ColorToTuple(Utils.RGBToColor(255, 0, 0, 255)))
                                if ImGui.ImageButton(f"{score[0].custom_skill.skill_name}", texture_file, 35,35):
                                    score[0].is_enabled = True
                                PyImGui.pop_style_var(1)
                                PyImGui.pop_style_color(1)
                                PyImGui.same_line(10, 0)
                                ImGui.DrawTexture(project_root + f"\\gui\\textures\\x.png", 20, 20)

                            PyImGui.table_next_column()
                            skill : CustomSkillUtilityBase = score[0]
                            unique_key = skill.custom_skill.skill_name
                            PyImGui.text(f"{skill.custom_skill.skill_name}")
                            PyImGui.same_line(0, 5)
                            expanded = unique_key in EXPANDED_SKILL_IDS
                            toggle_label = "[-]" if expanded else "[+]"
                            if PyImGui.small_button(f"{toggle_label}##expand_{unique_key}"):
                                if expanded:
                                    EXPANDED_SKILL_IDS.remove(unique_key)
                                else:
                                    EXPANDED_SKILL_IDS.add(unique_key)

                            black_color = Color(0, 0, 0, 255)
                            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, color)
                            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, color)
                            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, color)
                            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, black_color.to_tuple_normalized())
                            # clicked = PyImGui.button(f"{skill.custom_skill.skill_name}")
                            PyImGui.pop_style_color(4)
                            PyImGui.same_line(0, 5)
                            PyImGui.same_line(0, -1)

                            black_color = Color(0, 0, 0, 255)
                            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, UtilitySkillTypologyColor.get_color_from_typology(score[0].utility_skill_typology))
                            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, UtilitySkillTypologyColor.get_color_from_typology(score[0].utility_skill_typology))
                            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, UtilitySkillTypologyColor.get_color_from_typology(score[0].utility_skill_typology))
                            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, black_color.to_tuple_normalized())
                            PyImGui.button(f"score : {label_generic_utility(skill)}{score_text}")

                            PyImGui.pop_style_color(4)

                            if unique_key in EXPANDED_SKILL_IDS:
                                PyImGui.bullet_text("required ressource")
                                PyImGui.same_line(0, -1)
                                PyImGui.text_colored(f"{skill.mana_required_to_cast}",  Utils.RGBToNormal(27, 126, 246, 255))
                                allowed_names = [x.name for x in (skill.allowed_states or [])]
                                PyImGui.bullet_text(f"allowed in : {allowed_names}")
                                PyImGui.bullet_text(f"pre_check : {skill.are_common_pre_checks_valid(instance.get_final_state())}")
                                PyImGui.bullet_text(f"Slot:{skill.custom_skill.skill_slot}")
                                PyImGui.bullet_text(f"score max up-to:{skill.score_definition.score_definition_debug_ui()}")
                                buff_configuration: BuffConfigurationPerProfession | None = skill.get_buff_configuration()
                                if buff_configuration is not None:
                                    PyImGui.bullet_text(f"Buff configuration : ")
                                    for profession in BuffConfigurationPerProfession.ALL_PROFESSIONS:
                                        buff_configuration_per_profession = buff_configuration.get_by_profession(profession)
                                        texture_path =  py4gw_root_directory + f"Textures\\Profession_Icons\\[{profession.value}] - {profession.name}.png"
                                        icon_size = 26
                                        if buff_configuration_per_profession.is_activated:
                                            PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)  # 1px border
                                            PyImGui.push_style_color(PyImGui.ImGuiCol.Border, Utils.ColorToTuple(Utils.RGBToColor(3, 244, 60, 255)))
                                            if ImGui.ImageButton(f"deactivate_{unique_key}_{profession.name}", texture_path, icon_size, icon_size):
                                                buff_configuration_per_profession.is_activated = False
                                            ImGui.show_tooltip(f"Deactivate buff for {profession.name}")
                                            PyImGui.pop_style_var(1)
                                            PyImGui.pop_style_color(1)
                                        else:
                                            if ImGui.ImageButton(f"activate_{unique_key}_{profession.name}", texture_path, icon_size, icon_size):
                                                buff_configuration_per_profession.is_activated = True
                                            ImGui.show_tooltip(f"Activate buff for {profession.name}")
                                        PyImGui.same_line(0, 5)
                                skill.customized_debug_ui(instance.get_final_state())

                            PyImGui.table_next_row()
                        PyImGui.end_table()
                    PyImGui.end_tab_item()

                # Tab 2: Scoring (ordered by computed score)
                if PyImGui.begin_tab_item("scoring"):
                    PyImGui.text("order skills based on their calculated score")
                    sorted_scores = sorted(scores, key=lambda s: (s[1] is None, -s[1] if s[1] is not None else 0))
                    if PyImGui.begin_table("skills_compact", 3, PyImGui.TableFlags.RowBg | PyImGui.TableFlags.SizingStretchProp):
                        PyImGui.table_setup_column("Icon", PyImGui.TableColumnFlags.WidthFixed, 40)
                        PyImGui.table_setup_column("Name", PyImGui.TableColumnFlags.WidthStretch)
                        PyImGui.table_setup_column("Score", PyImGui.TableColumnFlags.WidthFixed, 70)
                        PyImGui.table_headers_row()
                        for util, sc in sorted_scores:
                            texture_file = util.custom_skill.get_texture(py4gw_root_directory, project_root)
                            PyImGui.table_next_row()
                            PyImGui.table_next_column()
                            ImGui.DrawTexture(texture_file, 35, 35)
                            PyImGui.table_next_column()
                            PyImGui.text(f"{util.custom_skill.skill_name}")
                            PyImGui.table_next_column()
                            score_text = f"{sc:06.4f}" if sc is not None else "Ø"
                            PyImGui.text(score_text)
                        PyImGui.end_table()
                    PyImGui.end_tab_item()

                PyImGui.end_tab_bar()
            PyImGui.end_child()



        if False and PyImGui.begin_child("x", size=(500, 600),border=True, flags=PyImGui.WindowFlags.HorizontalScrollbar):
            scores: list[tuple[CustomSkillUtilityBase, float | None]] = instance.get_all_scores()
            if PyImGui.begin_table("skill", 2, int(PyImGui.TableFlags.SizingStretchProp)):
                PyImGui.table_setup_column("A")
                PyImGui.table_setup_column("B")
                # PyImGui.table_headers_row()

            for score in scores:

                def label_generic_utility(utility: CustomSkillUtilityBase) -> str:
                    if utility.__class__.__name__ == "HeroAiUtility":
                        return f"HeroAI: "

                score_text = f"{score[1]:06.4f}" if score[1] is not None else "Ø"
                texture_file = score[0].custom_skill.get_texture(py4gw_root_directory, project_root)

                PyImGui.table_next_row()
                PyImGui.table_next_column()
                color = UtilitySkillTypologyColor.get_color_from_typology(score[0].utility_skill_typology)

                if score[0].is_enabled and CustomBehaviorParty().get_typology_is_enabled(score[0].utility_skill_typology) and instance.get_final_is_enabled():

                    PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
                    PyImGui.push_style_color(PyImGui.ImGuiCol.Border, color)

                    if ImGui.ImageButton(f"{score[0].custom_skill.skill_name}", texture_file, 35, 35):
                        score[0].is_enabled = False

                    PyImGui.pop_style_var(1)
                    PyImGui.pop_style_color(1)

                else:
                    PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
                    PyImGui.push_style_color(PyImGui.ImGuiCol.Border, Utils.ColorToTuple(Utils.RGBToColor(255, 0, 0, 255)))
                    if ImGui.ImageButton(f"{score[0].custom_skill.skill_name}", texture_file, 35,35):
                        score[0].is_enabled = True
                    PyImGui.pop_style_var(1)
                    PyImGui.pop_style_color(1)
                    PyImGui.same_line(10, 0)
                    ImGui.DrawTexture(project_root + f"\\gui\\textures\\x.png", 20, 20)

                # ImGui.DrawTexture(texture_file, 50, 50)
                PyImGui.table_next_column()

                skill : CustomSkillUtilityBase = score[0]
                slot_text = f"| slot {skill.custom_skill.skill_slot}" if skill.custom_skill.skill_slot > 0 else ""
                id_text = f"| id {skill.custom_skill.skill_id}" if skill.custom_skill.skill_id > 0 else ""

                PyImGui.text(f"{skill.custom_skill.skill_name}")

                # Black text color
                black_color = Color(0, 0, 0, 255)

                # Push button colors and text color
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, color)
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, color)
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, color)
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, black_color.to_tuple_normalized())

                # Create button
                # clicked = PyImGui.button(f"{skill.custom_skill.skill_name}")

                # Pop colors (4 colors now: button, hovered, active, text)
                PyImGui.pop_style_color(4)
                PyImGui.same_line(0, 5)
                # PyImGui.text(f"{id_text} {slot_text}")

                PyImGui.same_line(0, -1)

                # Black text color
                black_color = Color(0, 0, 0, 255)

                # Push button colors and text color
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, UtilitySkillTypologyColor.get_color_from_typology(score[0].utility_skill_typology))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, UtilitySkillTypologyColor.get_color_from_typology(score[0].utility_skill_typology))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, UtilitySkillTypologyColor.get_color_from_typology(score[0].utility_skill_typology))
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, black_color.to_tuple_normalized())

                # Create button
                clicked = PyImGui.button(f"score : {label_generic_utility(skill)}{score_text}",)

                # Pop colors (4 colors now: button, hovered, active, text)
                PyImGui.pop_style_color(4)

                if WITH_DETAIL:
                    PyImGui.bullet_text("required ressource")
                    PyImGui.same_line(0, -1)
                    PyImGui.text_colored(f"{skill.mana_required_to_cast}",  Utils.RGBToNormal(27, 126, 246, 255))
                    PyImGui.bullet_text(f"allowed in : {[x.name for x in skill.allowed_states]}")
                    PyImGui.bullet_text(f"pre_check : {skill.are_common_pre_checks_valid(instance.get_final_state())}")
                    PyImGui.bullet_text(f"Slot:{skill.custom_skill.skill_slot}")
                    PyImGui.bullet_text(f"score max up-to:{skill.score_definition.score_definition_debug_ui()}")

                    buff_configuration: BuffConfigurationPerProfession | None = skill.get_buff_configuration()
                    if buff_configuration is not None:
                        PyImGui.bullet_text(f"Buff configuration : ")
                        for profession in BuffConfigurationPerProfession.ALL_PROFESSIONS:

                            buff_configuration_per_profession = buff_configuration.get_by_profession(profession)
                            texture_path =  py4gw_root_directory + f"Textures\\Profession_Icons\\[{profession.value}] - {profession.name}.png"
                            icon_size = 26

                            if buff_configuration_per_profession.is_activated:
                                PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)  # 1px border
                                PyImGui.push_style_color(PyImGui.ImGuiCol.Border, Utils.ColorToTuple(Utils.RGBToColor(3, 244, 60, 255)))
                                if ImGui.ImageButton(f"deactivate_{skill.custom_skill.skill_id}_{profession.name}", texture_path, icon_size, icon_size):
                                    buff_configuration_per_profession.is_activated = False
                                ImGui.show_tooltip(f"Deactivate buff for {profession.name}")
                                PyImGui.pop_style_var(1)
                                PyImGui.pop_style_color(1)
                            else:
                                if ImGui.ImageButton(f"activate_{skill.custom_skill.skill_id}_{profession.name}", texture_path, icon_size, icon_size):
                                    buff_configuration_per_profession.is_activated = True
                                ImGui.show_tooltip(f"Activate buff for {profession.name}")
                            PyImGui.same_line(0, 5)

                    skill.customized_debug_ui(instance.get_final_state())

                PyImGui.table_next_row()

            PyImGui.end_table()
            PyImGui.end_child()












