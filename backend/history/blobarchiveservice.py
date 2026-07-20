import json
import logging
from datetime import datetime, timezone

from azure.core.exceptions import ResourceExistsError
from azure.identity.aio import DefaultAzureCredential
from azure.storage.blob.aio import BlobServiceClient


class BlobArchiveService:
    def __init__(self, account_name: str, container_name: str):
        self.account_name = account_name
        self.container_name = container_name
        self.account_url = f"https://{account_name}.blob.core.windows.net"

        self.credential = DefaultAzureCredential()
        self.blob_service_client = BlobServiceClient(
            account_url=self.account_url,
            credential=self.credential
        )
        self.container_client = self.blob_service_client.get_container_client(container_name)

    async def archive_chat_turn(self, archive_record: dict) -> str:
        now = datetime.now(timezone.utc)

        yyyy = now.strftime("%Y")
        mm = now.strftime("%m")
        dd = now.strftime("%d")

        user_id = archive_record["userId"]
        conversation_id = archive_record["conversationId"]
        assistant_message_id = archive_record["assistantMessage"]["id"]

        blob_name = (
            f"{yyyy}/{mm}/{dd}/"
            f"{user_id}/{conversation_id}/{assistant_message_id}.json"
        )

        blob_client = self.container_client.get_blob_client(blob_name)

        payload = json.dumps(
            archive_record,
            ensure_ascii=False,
            indent=2
        ).encode("utf-8")

        try:
            await blob_client.upload_blob(
                payload,
                overwrite=False
            )
            logging.info(f"Archived chat turn to blob: {blob_name}")
        except ResourceExistsError:
            logging.warning(f"Archive blob already exists, skipping: {blob_name}")

        return blob_name

    async def close(self):
        await self.blob_service_client.close()
        await self.credential.close()
