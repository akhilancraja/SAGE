"""
auto_chat.py - Custom startup logic for SAGE

This module overrides the default Oterm startup flow to automatically create
a new chat session using the 'mistral-7b-sage' model, bypassing the model
picker screen and preloading the interface with a named session and welcome message.
"""
from textual.widgets import TabPane
from oterm.app.widgets.chat import ChatContainer, ChatItem
from oterm.types import ChatModel
from oterm.store.store import Store

async def create_sage_session(tabs):
    store = await Store.get_store()

    chat_model = ChatModel(
        model="sage_v0.9",
        name="SAGE Session"
    )

    chat_id = await store.save_chat(chat_model)
    chat_model.id = chat_id

    pane = TabPane("SAGE Session", id=f"chat-{chat_id}")
    pane.compose_add_child(
        ChatContainer(
            chat_model=chat_model,
            messages=[],
        )
    )

    await tabs.add_pane(pane)
    tabs.active = f"chat-{chat_id}"
