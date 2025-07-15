# frontend/cli_interface.py
import os
from dotenv import load_dotenv
from foundry_sdk_phase.backend.agent_chat_service import AgentChatService


def banner() -> None:
    os.system("cls" if os.name == "nt" else "clear")
    print("🧠  R.E.A.L-Analyst — CLI")
    print("Type a message, or one of:")
    print("  new                -> create a new chat thread")
    print("  ls                 -> list threads")
    print("  switch <name>      -> switch to thread")
    print("  history            -> show current thread messages")
    print("  delete             -> delete current thread")
    print("  delete -A          -> delete ALL threads & start fresh")
    print("  quit               -> exit\n")


def main() -> None:
    load_dotenv()

    try:
        svc = AgentChatService()
    except Exception as exc:
        print(f"[ERROR] could not init AgentChatService: {exc}")
        return

    # ensure at least one thread
    svc.create_thread("thread-1")
    banner()

    while True:
        prompt = input(f"[{svc.current}]> ").strip()
        if not prompt:
            continue

        cmd, *args = prompt.split()

        if cmd in {"quit", "exit"}:
            print("Goodbye!")
            break

        # ───────── thread commands ─────────
        elif cmd == "new":
            name = f"thread-{len(svc.threads) + 1}"
            svc.create_thread(name)
            print(f"[NEW] switched to {name}")

        elif cmd == "ls":
            for t in svc.threads:
                marker = "•" if t == svc.current else " "
                print(f" {marker} {t}")

        elif cmd == "switch":
            if not args:
                print("Usage: switch <thread-name>")
                continue
            name = args[0]
            try:
                svc.switch(name)
                print(f"[SWITCH] now on {name}")
            except ValueError as e:
                print(e)

        elif cmd == "delete":
            if args and args[0] == "-A":          # **** delete ALL ****
                for t in list(svc.threads):
                    svc.delete_thread(t)
                svc.threads.clear()
                svc.create_thread("thread-1")
                print("[ALL THREADS DELETED] started fresh thread-1\n")
                banner()                          # re-show instructions
                continue

            # delete current only
            victim = svc.current
            svc.delete_thread(victim)
            print(f"[DELETED] {victim}")
            if svc.current:
                print(f"[SWITCHED] now on {svc.current}")
            else:
                svc.create_thread("thread-1")
                print("[NEW] started thread-1")

        elif cmd == "history":
            if not svc.current:
                print("[ERROR] No active thread. Create or switch first.\n")
                continue

            lines = svc.history()               # ← list[str]
            if not lines:
                print("[EMPTY] No messages yet.\n")
                continue

            print("\n--- Conversation History ---")
            for line in lines:
                print(line)                     # already plain text
            print("--------------------------------\n")
        # ───────── normal chat ─────────
        else:
            reply = svc.send(prompt)
            print(f"R.E.A.L-Analyst: {reply}\n")


if __name__ == "__main__":
    main()
