from projects.models.project_models import Projects
from core.services.image_service import process_image


class ProjectService:

    @staticmethod
    def create_project(validated_data):
        image = validated_data.get("image")

        if image:
            validated_data["image"] = process_image(image)

        return Projects.objects.create(**validated_data)

    @staticmethod
    def update_project(instance, validated_data):
        image = validated_data.get("image")

        if image:
            validated_data["image"] = process_image(image)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
