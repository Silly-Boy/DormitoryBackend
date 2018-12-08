from typing import List

from .util import http, get_request_json, get_filter_condition, generate_pagination_list
from .global_obj import app
from .model import Dormitory, Building, ElectricityMeter, WaterMeter
from .permission import get_permission_condition, check_permission_condition, PermissionDenied


dormitory_normal_properties = {
    "number": {
        "type": "string",
        "pattern": "^[0-9]+$",
    },
    "building": {
        "type": "integer",
    },
    "electricity_meter": {
        "type": "integer",
    },
    "water_meter": {
        "type": "integer",
    },
}


dormitory_filter_properties = dict(dormitory_normal_properties, id={
    "type": "integer",
})


dormitory_updatable_properties = dict(dormitory_normal_properties)


def get_dormitories(filter: dict, allowed: List[str]):
    return Dormitory.select().where(
        get_filter_condition(filter, Dormitory)
        & get_permission_condition(allowed, Dormitory)
    )


def generate_dormitory_info(dormitory: Dormitory):
    return {
        "id": dormitory.id,
        "number": dormitory.number,
        "building": {
            "id": dormitory.building_id,
            "name": dormitory.building.name,
        },
        "electricity_meter": dormitory.electricity_meter_id,
        "water_meter": dormitory.water_meter_id,
    }


@app.route("/dormitory/list", methods=["POST"])
def get_dormitory_list():
    instance = get_request_json(schema={
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "page": {
                "type": "integer",
            },
            "limit": {
                "type": "integer",
            },
            "filter": {
                "type": "object",
                "properties": dormitory_filter_properties,
                "additionalProperties": False,
            },
        },
        "required": ["page", "limit", "filter"],
        "additionalProperties": False,
    })
    dormitories = get_dormitories(instance["filter"], ["Management", "Self"])
    return http.Success(result=generate_pagination_list(
        objs=dormitories,
        instance_generator=generate_dormitory_info,
        page=instance["page"],
        limit=instance["limit"]
    ))


def obj_process(obj: dict):
    if "building" in obj:
        building_id = obj["building"]
        building = Building.get(id=building_id)
        check_permission_condition(building, get_permission_condition(["Management"], Building))

    if "electricity_meter" in obj:
        electricity_meter_id = obj["electricity_meter"]
        electricity_meter = ElectricityMeter.get(id=electricity_meter_id)
        check_permission_condition(electricity_meter, get_permission_condition(["Management"], ElectricityMeter))

    if "water_meter" in obj:
        water_meter_id = obj["water_meter"]
        water_meter = WaterMeter.get(id=water_meter_id)
        check_permission_condition(water_meter, get_permission_condition(["Management"], WaterMeter))


@app.route("/dormitory/update", methods=["POST"])
def update_dormitory_info():
    instance = get_request_json(schema={
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "filter": {
                "type": "object",
                "properties": dormitory_filter_properties,
                "additionalProperties": False,
            },
            "obj": {
                "type": "object",
                "properties": dormitory_updatable_properties,
                "additionalProperties": False,
            },
        },
        "required": ["filter", "obj"],
        "additionalProperties": False,
    })
    obj_process(instance["obj"])

    allow_read_dormitory = get_dormitories(instance["filter"], ["Management", "Self"])
    if allow_read_dormitory.count() < 1:
        raise Dormitory.DoesNotExist()

    allow_write_dormitory = get_dormitories(instance["filter"], ["Management"])
    if allow_write_dormitory.count() < 1:
        raise PermissionDenied()

    for dormitory in allow_write_dormitory:
        for(key, value) in instance["obj"].items():
            setattr(dormitory, key, value)
        dormitory.save()

    return http.Success()


@app.route("/dormitory/create", methods=["POST"])
def create_dormitory():
    instance = get_request_json(schema={
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "obj": {
                "type": "object",
                "properties": dormitory_updatable_properties,
                "required": list(dormitory_updatable_properties.keys()),
                "additionalProperties": False,
            },
        },
        "required": ["obj"],
        "additionalProperties": False,
    })
    obj_process(instance["obj"])

    dormitory = Dormitory()
    for (key, value) in instance["obj"].items():
        setattr(dormitory, key, value)

    dormitory.save()
    return http.Success()
