from common.services.image_service import process_image
from home.models import FloorPlan


class FloorPlanService:
    @staticmethod
    def create_floorplan(validated_data):
        image = validated_data.get("image")

        if image:
            validated_data["image"] = process_image(image)

        return FloorPlan.objects.create(**validated_data)
