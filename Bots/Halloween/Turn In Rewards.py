from Py4GWCoreLib import Botting, Py4GW, Quest, GLOBAL_CACHE, Routines

bot = Botting("Turn In Rewards")

STEWARD_ID = 147
STEWARD_POSITION = (5332.0, 9048.0)
DIALOG_QUEST_SELECT = 0x846303
DIALOG_QUEST_ACCEPT = 0x846301
DIALOG_QUEST_COLLECT_REWARD = 0x846307
QUEST_ID = 1123
MAX_ITERATIONS = 5000
MOB_STOPPERS_PER_QUEST = 3


# ---------- Utility & Settings Helpers ----------
def get_user_settings():
    if not hasattr(bot.config, "user_vars"):
        bot.config.user_vars = {}
    uv = bot.config.user_vars
    uv.setdefault("desired_mobstopper_quantity", 402)
    uv.setdefault("completed_mobstopper_cycles", 0)
    return uv

def deposit_all_gold():
    gold_on_char = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()
    if gold_on_char > 0:
        GLOBAL_CACHE.Inventory.DepositGold(gold_on_char)
        yield from Routines.Yield.wait(250)
    else:
        yield

def AddCheckQuotaStep(step_name="Check Quota"):
    def _check():
        uv = get_user_settings()
        desired = int(uv.get("desired_mobstopper_quantity", 10))
        completed = int(uv.get("completed_mobstopper_cycles", 0))

        if completed >= desired:
            fsm = bot.config.FSM
            fsm.jump_to_state_by_name("Stop")
            fsm.resume()
        yield

    bot.States.AddCustomState(_check, step_name)


# ---------- Main Bot Routine ----------
def create_bot_routine(bot: Botting) -> None:
    bot.States.AddHeader("Mobstopper Collection Started")

    uv = get_user_settings()
    done = int(uv.get("completed_mobstopper_cycles", 0))
    desired = int(uv.get("desired_mobstopper_quantity", 402))

    if done >= desired:
        bot.States.AddHeader("Completed!")
        bot.Stop()
        return

    bot.States.AddHeader("Travel to Lion's Arch")
    bot.Map.Travel(target_map_id=808)
    bot.States.AddHeader("Deposit Gold")
    bot.States.AddCustomState(deposit_all_gold, "Deposit Gold")
    bot.States.AddHeader("Take Quest")
    bot.Move.XY(*STEWARD_POSITION, "Move to Steward")
    bot.Dialogs.WithModel(STEWARD_ID, DIALOG_QUEST_SELECT, "Talk to Steward")
    bot.Dialogs.WithModel(STEWARD_ID, DIALOG_QUEST_ACCEPT, "Accept Quest")
    bot.Wait.ForTime(50)
    bot.States.AddHeader(f"Turned in {done}/{desired} Mobstoppers")
    bot.Dialogs.WithModel(STEWARD_ID, DIALOG_QUEST_COLLECT_REWARD, "Collect Reward")
    bot.States.AddHeader("Rejoin LA")
    bot.Map.TravelGH()
    bot.Map.LeaveGH()

    uv["completed_mobstopper_cycles"] = done + MOB_STOPPERS_PER_QUEST
    bot.States.JumpToStepName("[H]Deposit Gold_3")

    fsm = bot.config.FSM
    fsm.resume()


bot.SetMainRoutine(create_bot_routine)


# ---------- Entry Point ----------

def main():
    bot.Update()
    bot.UI.draw_window(icon_path=None)


if __name__ == "__main__":
    main()
