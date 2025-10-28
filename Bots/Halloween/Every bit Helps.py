from Py4GWCoreLib import *
from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType
from Py4GWCoreLib.py4gwcorelib_src.ActionQueue import ActionQueueManager

bot = Botting("Skeleton Collector")

MAX_ITERATIONS = 5000
EMBARK_BEACH_ID = 857
TEMPLE_OF_THE_AGES_ID = 138
THE_UNDERWORLD_ID = 72
GRENTH_STATUE_POSITON = (-4035.76, 19809.09)

VOICE_OF_GRENTH_POSITION = (-4124.00, 19829.00)

TRAP_PLACED = False

VOICE_OF_GRENTH_ID = 1945
ENTER_UW_DIALOG = 0x85
ENTER_UW_ACCEPT = 0x86
UW_SCROLL_ID = 3746

SKELETON_AGENT_MODEL_ID = 2342
SKELETON_TRAP_ID = 32558


def get_other_accounts():
    me = GLOBAL_CACHE.Player.GetAccountEmail()
    out = []
    for acc in GLOBAL_CACHE.ShMem.GetAllAccountData() or []:
        if not acc or not getattr(acc, "AccountEmail", None):
            continue
        if acc.AccountEmail == me:
            continue
        out.append(acc.Email if hasattr(acc, "Email") else acc.AccountEmail)
    return out


def broadcast_item(model_id: int, repeat=5, use_locally=True, delay=100):
    sender = GLOBAL_CACHE.Player.GetAccountEmail()
    for email in get_other_accounts():
        GLOBAL_CACHE.ShMem.SendMessage(sender_email=sender, receiver_email=email, command=SharedCommandType.UseItem, params=(float(model_id), float(repeat)), )
    if use_locally:
        for _ in range(max(1, int(repeat))):
            item_id = GLOBAL_CACHE.Item.GetItemIdFromModelID(model_id)
            if not item_id:
                break
            GLOBAL_CACHE.Inventory.UseItem(item_id)
            yield from Routines.Yield.wait(delay)
    yield


def broadcast_skill(skill_name: str, cast_locally=True, delay=300):
    skill_id = int(GLOBAL_CACHE.Skill.GetID(skill_name) or 0)
    if not skill_id:
        return
    target_id = Player.GetTargetID()
    if not target_id:
        return
    sender = GLOBAL_CACHE.Player.GetAccountEmail()
    for email in get_other_accounts():
        GLOBAL_CACHE.ShMem.SendMessage(sender_email=sender, receiver_email=email, command=SharedCommandType.UseSkill, params=(float(target_id), float(skill_id)), )
    if cast_locally:
        slot = int(GLOBAL_CACHE.SkillBar.GetSlotBySkillID(skill_id) or 0)
        if 1 <= slot <= 8:
            yield from Routines.Yield.Skills.CastSkillSlot(slot, aftercast_delay=delay)
    yield


def withdraw_gold(target_gold=1000):
    gold_on_char = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()
    if gold_on_char < target_gold:
        to_withdraw = target_gold - gold_on_char
        GLOBAL_CACHE.Inventory.WithdrawGold(to_withdraw)
        yield from Routines.Yield.wait(250)


def _set_trap_used(val: bool):
    global TRAP_PLACED
    TRAP_PLACED = bool(val)

def _mark_trap_done():
    _set_trap_used(True)
    yield

def _target_model_strict(model_id: int, checks: int = 2, settle_ms: int = 80) -> bool:
    for _ in range(max(1, checks)):
        bot.Target.Model(model_id)
        bot.Wait.ForTime(settle_ms)
        tid = Player.GetTargetID()
        if tid and GLOBAL_CACHE.Agent.GetModelID(tid) == model_id:
            return True
    return False

def _kneel():
    Player.SendChatCommand("kneel")
    yield from Routines.Yield.wait(10)

def create_bot_routine(bot: Botting) -> None:

    bot.States.AddHeader("Skeleton Collection Started")
    bot.Properties.Disable("auto_inventory_management")
    bot.Properties.Disable("auto_loot")
    bot.Properties.Disable("hero_ai")
    bot.Properties.Disable("pause_on_danger")
    bot.Properties.Enable("auto_combat")
    bot.Templates.Pacifist()

    bot.States.AddHeader("Moving to Grenth Statue")
    bot.States.AddCustomState(withdraw_gold, "Withdraw Gold")
    bot.Wait.ForTime(10)
    bot.Move.XY(*GRENTH_STATUE_POSITON, "Move to Grenth Statue")
    bot.States.AddHeader("Speaking With Voice of Grenth for Entering the Underworld")
    bot.States.AddCustomState(_kneel, "Kneel")
    bot.Wait.ForTime(2000)

    bot.Dialogs.WithModel(VOICE_OF_GRENTH_ID, ENTER_UW_DIALOG, "Yes. To serve Grenth.")
    bot.Wait.ForMapLoad(target_map_id=THE_UNDERWORLD_ID)


    bot.States.AddHeader("Killing Skeleton")
    bot.Target.Model(SKELETON_AGENT_MODEL_ID)
    bot.States.AddCustomState(lambda: broadcast_skill("Shroud_of_Distress"), "Broadcast Dash Shroud_of_Distress")
    bot.Wait.ForTime(1010)
    bot.States.AddCustomState(lambda: broadcast_skill("Dash"), "Broadcast Dash")
    bot.States.AddCustomState(lambda: broadcast_skill("Deaths_Charge"), "Broadcast Deaths_Charge")
    bot.Wait.ForTime(3600)
    bot.States.AddCustomState(lambda: broadcast_skill("Light_of_Deldrimor"), "Broadcast Light_of_Deldrimor")
    bot.Wait.ForTime(1100)

    bot.States.AddHeader("Using Skeleton Trap")
    _set_trap_used(False)
    bot.Wait.ForTime(100)
    bot.States.AddCustomState(lambda: broadcast_skill("By_Urals_Hammer"), "Broadcast By_Urals_Hammer")
    bot.Wait.ForTime(10)
    bot.States.AddCustomState(lambda: broadcast_item(SKELETON_TRAP_ID, repeat=1, use_locally=True, delay=0), "Place Skeleton Trap")
    bot.States.AddCustomState(_mark_trap_done, "Mark Trap Used")
    bot.Wait.UntilCondition(lambda: TRAP_PLACED)
    bot.States.AddHeader("Resigning Party")
    bot.Multibox.ResignParty()
    bot.Wait.ForTime(1000)
    bot.Wait.ForMapLoad(target_map_id=TEMPLE_OF_THE_AGES_ID)
    bot.States.AddHeader("Resetting")
    ActionQueueManager().ResetAllQueues()
    bot.States.JumpToStepName("[H]Moving to Grenth Statue_2")

bot.SetMainRoutine(create_bot_routine)


def main():
    bot.Update()
    bot.UI.draw_window(icon_path=None)


if __name__ == "__main__":
    main()
