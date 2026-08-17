from sqlalchemy import func, select

from app.models import ChatFile


class FileGuardService:

    @staticmethod
    async def validate_file_upload(
        db,
        user,
        subscription,
        file_size_bytes: int,
    ):
        plan = subscription.plan

        result = await db.execute(
            select(
                func.count(ChatFile.id),
                func.coalesce(
                    func.sum(ChatFile.file_size),
                    0
                )
            ).where(
                ChatFile.user_id == user.id
            )
        )

        file_count, storage_used = result.one()

        if (
            plan.max_files is not None
            and file_count >= plan.max_files
        ):
            raise ValueError(
                "Maximum file count reached"
            )

        new_storage = storage_used + file_size_bytes

        if (
            plan.max_storage_mb is not None
            and new_storage >
            plan.max_storage_mb * 1024 * 1024
        ):
            raise ValueError(
                "Storage limit exceeded"
            )