from base_entities import SizeInfo, ProductInfo, SizeInfoType
from helpers import parse_weight_info_with_validation


def test():
    data1 = {
        "normalized_title": "каша вівсяна з лохиною, насінням чіа та чорницею",
        "title": "Каша вівсяна «Премія»® з лохиною, насінням чіа та чорницею",
        "unit": None,
        "category_id": "2",
        "producer": {
            "trademark": "Премія"
        },
        "weight": "40г",
        "bundle": None,
        "volume": None
    }
    output: SizeInfo = parse_weight_info_with_validation(ProductInfo.parse_obj(data1))
    assert output == SizeInfo(value=30, unit="г", type=SizeInfoType.Mass)


if __name__ =="__main__":
    test()
