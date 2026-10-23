import json
import re
import traceback
from asyncio import TimeoutError
from dataclasses import asdict, dataclass, field
from typing import Self, override

import disnake
from disnake.ext.tasks import loop


@dataclass
class Config:
    FILENAME = "config.json"

    token: str = field(repr=False)
    owner_id: int
    button_timeout: float
    head_ignore: dict[int, int]

    @classmethod
    def from_file(cls, filename: str = FILENAME) -> Self:
        with open(filename, encoding="u8") as f:
            data = json.load(f)
            return cls(
                token=data["token"],
                owner_id=data["owner_id"],
                button_timeout=data["interaction_timeout"],
                head_ignore={int(k): v for k, v in data["head_ignore"]},
            )

    def to_file(self, filename: str = FILENAME) -> None:
        with open(filename, "w", encoding="u8") as f:
            data = asdict(self)
            data["head_ignore"] = list(data["head_ignore"].items())
            json.dump(data, f, indent=4)


config = Config.from_file()


def parse_numbers(content: str) -> list[str]:
    return re.findall(r"^\d+", content, re.ASCII | re.MULTILINE)  # (?=$|\s)


class DeleteButtonView(disnake.ui.View):
    def __init__(self, message: disnake.Message, *, timeout: float | None = 60.0):
        super().__init__(timeout=timeout)
        self.message = message

    @override
    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        if inter.author.id != config.owner_id:
            await inter.response.send_message("<:whyareyougay:775043501578649641>", ephemeral=True)
            return False
        return True

    @disnake.ui.button(emoji="<:haram:984896655444836403>", label="Delete message")
    async def delete_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await self.message.delete()
        button.emoji, button.label, button.disabled = "✅", "Message deleted", True
        self.remove_item(self.skip_button)
        await inter.response.edit_message(view=self)

    @disnake.ui.button(emoji="<:halal:984896652093583360>", label="Smart™ skip message")
    async def skip_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        button.emoji, button.label, button.disabled = "✅", "Message skipped", True
        self.remove_item(self.delete_button)
        await inter.response.edit_message(view=self)


async def ask_delete(
    client: disnake.Client, channel: disnake.abc.Messageable, message: disnake.Message, head: int
) -> bool:
    "Return True if user pressed delete button, else return False"
    view = DeleteButtonView(message, timeout=config.button_timeout)
    dialog = await channel.send(
        view=view,
        embed=disnake.Embed(description=f"Found an error in {message.jump_url}")
        .add_field("Expected", head)
        .add_field("Actual", message.content[:100]),
    )

    def check(inter: disnake.MessageInteraction) -> bool:
        return inter.author.id == config.owner_id and inter.component.custom_id in {
            view.delete_button.custom_id,
            view.skip_button.custom_id,
        }

    try:
        return (
            await client.wait_for("button_click", check=check, timeout=config.button_timeout)
        ).component.custom_id == view.delete_button.custom_id
    except TimeoutError:
        view.delete_button.disabled, view.skip_button.disabled = True, True
        await dialog.edit(view=view)
        raise SystemExit("Stopping due to inactivity.")


@loop(count=1)
async def scan(client: disnake.Client) -> None:
    await client.wait_until_ready()
    if not (L1 := client.get_guild(676889696302792774)):
        return
    RoadTo69420 = L1.get_thread(940355083860844575)
    Roadworks = L1.get_thread(1134345708992995448)
    if not RoadTo69420 or not Roadworks:
        return

    try:
        print("Scanning messages...")
        await Roadworks.send("Scanning messages...")
        async with Roadworks.typing():
            head = 1
            async for message in RoadTo69420.history(limit=None, oldest_first=True):
                if head in config.head_ignore:
                    head += config.head_ignore[head]
                    continue

                match message.type:
                    case disnake.MessageType.default | disnake.MessageType.reply:
                        pass
                    case disnake.MessageType.pins_add:
                        await message.delete()
                        continue
                    case _:
                        if head > 911:
                            await Roadworks.send(f"{message.jump_url} {message.system_content}")
                        continue

                numbers = parse_numbers(message.content)
                if len(numbers) != message.content.count("\n") + 1:
                    if not await ask_delete(client, Roadworks, message, head):
                        if tuple(range(head, head + len(numbers))) == tuple(map(int, numbers)):
                            head += len(numbers)
                    continue

                blockbuf = 0
                for number in map(int, numbers):
                    if number != head:
                        head -= blockbuf
                        if not await ask_delete(client, Roadworks, message, head):
                            head += len(numbers)
                        break
                    head += 1
                    blockbuf += 1
            else:
                print("No errors!")
                await Roadworks.send("No errors!")
    finally:
        await client.close()


def main() -> None:
    client = disnake.Client()
    scan.start(client)
    client.run(config.token)


if __name__ == "__main__":
    main()
