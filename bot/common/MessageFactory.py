""""""

from bot.models.chat import ChatMessage, RichChatMessage
from bot.services.ai.models import FourSidesAnalysis


class MessageFactory:

    @staticmethod
    def transform_message(
        base: ChatMessage, analysis: FourSidesAnalysis
    ) -> RichChatMessage:
        """"""
        return RichChatMessage(
            id=base.id,
            message=base.message,
            time=base.time,
            sender=analysis.sender,
            receivers=analysis.receivers,
            factual_information=analysis.factual_information,
            self_revelation=analysis.self_revelation,
            relationship=analysis.relationship,
            appeal=analysis.appeal,
            linked_messages=analysis.linked_messages,
        )
