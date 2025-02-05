""""""

from bot.models.chat import ChatMessage, RichChatMessage
from bot.services.ai.models import FourSidesAnalysis


class MessageFactory:

    @staticmethod
    def transform_message(base: ChatMessage, analysis: FourSidesAnalysis) -> RichChatMessage:
        """"""
        return RichChatMessage(
            id=base.id,
            message=base.message,
            time=base.time,
            sender=analysis.sender,
            receiver=analysis.receiver,
            factual_information=analysis.factual_information,
            self_revelation=analysis.self_revelation,
            relationship=analysis.relationship,
            appeal=analysis.appeal,
            linked_messages=analysis.related_message_ids,
        )
