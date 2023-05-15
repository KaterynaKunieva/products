from base_entities import SizeInfo, ProductInfo, SizeInfoType
from helpers import parse_weight_info_with_validation, normalize_title


def test():
    data1 = {
        "normalized_title": "крем з бальзамічний оцтом з модени",
        "title": "Крем Metro Chef з бальзамічний оцтом з Модени 250мл",
        "category_id": "balsamic-vinegar-metro",
        "price": 89.8,
        "weight": "250.0",
        "bundle": 1,
        "volume": 250.0,
        "weight_info": {
          "value": 250.0,
          "unit": "",
          "type": "quantity"
        },
        "producer": {
          "trademark": "Metro Chef",
          "trademark_slug": "metro-chef"
        },
        "description": "",
        "slug": "krem-metro-shef-250ml-italiia",
        "web_url": "https://metro.zakaz.ua/uk/products/krem-metro-shef-250ml-italiia--04333465133829/"
    }
    output: SizeInfo = parse_weight_info_with_validation(ProductInfo.parse_obj(data1))
    assert output == SizeInfo(value=250, unit="мл", type=SizeInfoType.Capacity)

    data2 = {
        "normalized_title": "оцет colavita condimento italiano bianco винний бiлий",
        "title": "Оцет Colavita Condimento Italiano Bianco винний бiлий 5,4% 0,5л",
        "category_id": "balsamic-vinegar-metro",
        "price": 118.69,
        "weight": "500.0",
        "bundle": 1,
        "volume": 500.0,
        "weight_info": {
            "value": 500.0,
            "unit": "",
            "type": "quantity"
        },
        "producer": {
            "trademark": "колавіта",
            "trademark_slug": "colavita"
        },
        "description": "",
        "slug": "otset-kolavita-500ml",
        "web_url": "https://metro.zakaz.ua/uk/products/otset-kolavita-500ml--08001876552541/"
    }
    output: SizeInfo = parse_weight_info_with_validation(ProductInfo.parse_obj(data2))
    assert output == SizeInfo(value=0.5, unit="л", type=SizeInfoType.Capacity)

    data3 = {
        "normalized_title": "оцет бальзамічний з модени",
        "title": "Оцет Metro Chef бальзамічний з Модени 1л",
        "category_id": "balsamic-vinegar-metro",
        "price": 142.9,
        "weight": "1400.0",
        "bundle": 1,
        "volume": 1000.0,
        "weight_info": {
            "value": 1400.0,
            "unit": "",
            "type": "quantity"
        },
        "producer": {
            "trademark": "Metro Chef",
            "trademark_slug": "metro-chef"
        },
        "description": "",
        "slug": "otset-metro-shef-1000ml",
        "web_url": "https://metro.zakaz.ua/uk/products/otset-metro-shef-1000ml--04337182071891/"
    }
    output: SizeInfo = parse_weight_info_with_validation(ProductInfo.parse_obj(data3))
    assert output == SizeInfo(value=1, unit="л", type=SizeInfoType.Capacity)

    data4 = {
        "normalized_title": "оцет kuhne бальзаміко винний",
        "title": "Оцет Kuhne Бальзаміко винний 500мл",
        "category_id": "balsamic-vinegar-metro",
        "price": 182.41,
        "weight": "946.0",
        "bundle": 1,
        "volume": 500.0,
        "weight_info": {
            "value": 946.0,
            "unit": "",
            "type": "quantity"
        },
        "producer": {
            "trademark": "Kühne",
            "trademark_slug": "kuhne"
        },
        "description": "5% оцтової кислоти, продукт натурального бродіння. Оригінальний італійський оцет з виноградного соку та білого вина. Білий бальзамовий оцет має помірний пряний смак і аромат оригінального італійського оцту, виробленого з винограду. Він ідеально підходить для приготування зелених салатів, а також для додавання кінцевого штриху легким соусам, м'ясу та рибі. Непрозорість та осад не знижують якості продукту.",
        "slug": "otset-kiune-500ml",
        "web_url": "https://metro.zakaz.ua/uk/products/otset-kiune-500ml--04012200168608/"
    }
    output: SizeInfo = parse_weight_info_with_validation(ProductInfo.parse_obj(data4))
    assert output == SizeInfo(value=500, unit="мл", type=SizeInfoType.Capacity)

    data5 = {
        "normalized_title": "кошик для хлібу круглий 3шт",
        "title": "Кошик для хлібу Aro круглий 18х5см 3шт",
        "category_id": "bread-bins-metro",
        "price": 129.9,
        "weight": "0",
        "bundle": 1,
        "volume": 0,
        "producer": {
            "trademark": "Aro",
            "trademark_slug": "aro"
        },
        "description": "",
        "slug": "korzina-aro",
        "web_url": "https://metro.zakaz.ua/uk/products/korzina-aro--04337182498056/"
    }
    output: SizeInfo = parse_weight_info_with_validation(ProductInfo.parse_obj(data5))
    assert output == SizeInfo(value=90.0, unit="см", type=SizeInfoType.Length)

    data6 = {
        "normalized_title": "кошик для хліба 3шт",
        "title": "Кошик Aro для хліба 24х18см 3шт",
        "category_id": "bread-bins-metro",
        "price": 179.9,
        "weight": "230.0",
        "bundle": 1,
        "volume": 0,
        "weight_info": {
            "value": 230.0,
            "unit": "",
            "type": "quantity"
        },
        "producer": {
            "trademark": "Aro",
            "trademark_slug": "aro"
        },
        "description": "",
        "slug": "korzina-aro",
        "web_url": "https://metro.zakaz.ua/uk/products/korzina-aro--04337182498070/"
    }
    output: SizeInfo = parse_weight_info_with_validation(ProductInfo.parse_obj(data6))
    assert output == SizeInfo(value=432.0, unit="см", type=SizeInfoType.Length)
    #
    data7 = {
        "normalized_title": "корзина для хлібу кругла 6шт",
        "title": "Корзина для хлібу Aro кругла 23см 6шт",
        "category_id": "bread-bins-metro",
        "price": 219.9,
        "weight": "0",
        "bundle": 1,
        "weight_info": {
            "value": 23.0,
            "unit": "см",
            "type": "quantity"
        },
        "producer": {
            "trademark": "Aro",
            "trademark_slug": "aro"
        },
        "description": "",
        "slug": "korzina-aro",
        "web_url": "https://metro.zakaz.ua/uk/products/korzina-aro--04337182498018/"
    }
    output: SizeInfo = parse_weight_info_with_validation(ProductInfo.parse_obj(data7))
    assert output == SizeInfo(value=23.0, unit="см", type=SizeInfoType.Length)

    data8 = {
        "normalized_title": "кошик для хлібу квадратний",
        "title": "Кошик для хлібу Metro Professional квадратний 25х25х8см",
        "category_id": "bread-bins-metro",
        "price": 139.9,
        "weight": "300.0",
        "bundle": 1,
        "weight_info": {
          "value": 300.0,
          "unit": "",
          "type": "quantity"
        },
        "producer": {
          "trademark": "Metro Professional",
          "trademark_slug": "metro-professional"
        },
        "description": "",
        "slug": "korzina-metro-profeshinal",
        "web_url": "https://metro.zakaz.ua/uk/products/korzina-metro-profeshinal--04337182498278/"
    }
    output: SizeInfo = parse_weight_info_with_validation(ProductInfo.parse_obj(data8))
    assert output == SizeInfo(value=5000, unit="см", type=SizeInfoType.Length)

    data9 = {
        "normalized_title": "печериці закусочні",
        "title": "Печериці Верес закусочні 260г",
        "category_id": "canned-mushrooms-metro",
        "price": 71.97,
        "weight": "466.0",
        "bundle": 1,
        "weight_info": {
            "value": 466.0,
            "unit": "",
            "type": "quantity"
        },
        "producer": {
            "trademark": "Верес",
            "trademark_slug": "veres"
        },
        "description": "Мариновані шампіньйони у цільних зернятах гірчиці, часнику та спеціях – це улюблена закуска на домашньому столі або на пікніку. Добірні грибочки із власної грибниці «Верес» у смачному маринаді давно вподобали споживачі. А ще, з нашими шампіньйонами вдаються складні салати із пікантною ноткою. Спробуйте, вам сподобається!",
        "slug": "gribi-shampinioni-veres-260g-ukrayina",
        "web_url": "https://metro.zakaz.ua/uk/products/gribi-shampinioni-veres-260g-ukrayina--04823105400164/"
    }
    output: SizeInfo = parse_weight_info_with_validation(ProductInfo.parse_obj(data9))
    assert output == SizeInfo(value=260.0, unit="г", type=SizeInfoType.Mass)

    data10 = {
        "normalized_title": "опеньки долина бажань мариновані",
        "title": "Опеньки Долина Бажань мариновані 1700мл",
        "category_id": "canned-mushrooms-metro",
        "price": 348.63,
        "weight": "930.0",
        "bundle": 1,
        "volume": 1700.0,
        "weight_info": {
            "value": 930.0,
            "unit": "",
            "type": "quantity"
        },
        "producer": {
            "trademark": "Долина Желаний",
            "trademark_slug": "dolina-zhelanii"
        },
        "description": "",
        "slug": "gribi-openki-dolina-bazhan-930g",
        "web_url": "https://metro.zakaz.ua/uk/products/gribi-openki-dolina-bazhan-930g--04820086924474/"
    }
    output: SizeInfo = parse_weight_info_with_validation(ProductInfo.parse_obj(data10))
    assert output == SizeInfo(value=1700.0, unit="мл", type=SizeInfoType.Capacity)

    data11 = {
        "normalized_title": "шампіньйони marinado варені різані",
        "title": "Шампіньйони Marinado варені різані 1кг",
        "category_id": "canned-mushrooms-metro",
        "price": 208.71,
        "weight": "1000.0",
        "bundle": 1,
        "weight_info": {
            "value": 1000.0,
            "unit": "",
            "type": "quantity"
        },
        "producer": {
            "trademark": "маринадо",
            "trademark_slug": "marinado"
        },
        "description": "",
        "slug": "shampinioni-marinado-1000g",
    }
    output: SizeInfo = parse_weight_info_with_validation(ProductInfo.parse_obj(data11))
    assert output == SizeInfo(value=1.0, unit="кг", type=SizeInfoType.Mass)

    data11 = {
        "normalized_title": "шампіньйони різані",
        "title": "Шампіньйони Rio різані 2,95кг",
        "category_id": "canned-mushrooms-metro",
        "price": 495.97,
        "weight": "4050.0",
        "bundle": 1,
        "volume": 3000.0,
        "weight_info": {
            "value": 4050.0,
            "unit": "",
            "type": "quantity"
        },
        "producer": {
            "trademark": "RIO",
            "trademark_slug": "rio"
        },
        "description": "Шампіньйони різані та пастеризовані з додаванням лише солі. Підходять для приготування різних холодних та гарячих страв.",
        "slug": "gribi-shampinioni-rio-3000ml",
    }
    output: SizeInfo = parse_weight_info_with_validation(ProductInfo.parse_obj(data11))
    assert output == SizeInfo(value=2.95, unit="кг", type=SizeInfoType.Mass)

    data12 = {
        "normalized_title": "напій енергетичний original",
        "title": "Напій енергетичний Non Stop Original 0,5л",
        "category_id": "energy-drinks-metro",
        "price": 772.2,
        "weight": "245.0",
        "bundle": 24,
        "volume": 500.0,
        "weight_info": {
            "value": 245.0,
            "unit": "",
            "type": "quantity"
        },
        "producer": {
            "trademark": "Non Stop",
            "trademark_slug": "non-stop"
        },
        "description": "",
        "slug": "energetik-non-stop-ukrayina",
    }
    output: SizeInfo = parse_weight_info_with_validation(ProductInfo.parse_obj(data12))
    assert output == SizeInfo(value=0.5, unit="л", type=SizeInfoType.Capacity)

    data13 = {
        "normalized_title": "напій енергетичний monster mango loco",
        "title": "Напій енергетичний Monster Mango Loco 0,355л",
        "category_id": "energy-drinks-metro",
        "price": 589.68,
        "weight": "355.0",
        "bundle": 12,
        "volume": 355.0,
        "weight_info": {
            "value": 355.0,
            "unit": "",
            "type": "quantity"
        },
        "producer": {
            "trademark": "Monster energy",
            "trademark_slug": "monster-energy"
        },
        "description": "",
        "slug": "energetik-355ml",
        "web_url": "https://metro.zakaz.ua/uk/products/energetik-355ml--05060751213079/"
    }
    output: SizeInfo = parse_weight_info_with_validation(ProductInfo.parse_obj(data13))
    assert output == SizeInfo(value=0.355, unit="л", type=SizeInfoType.Capacity)

    data14 = {
        "normalized_title": "бастурма з яловичини класична сировялена в/ґ",
        "title": "Бастурма з яловичини М'ясна гільдія Класична сиров'ялена в/ґ",
        "category_id": "basturma-metro",
        "price": 1074.6,
        "weight": "0",
        "bundle": 1,
        "unit": "кг",
        "weight_info": {
            "value": 0.0,
            "unit": "",
            "type": "quantity"
        },
        "producer": {
            "trademark": "М'ясна Гільдія",
            "trademark_slug": "miasna-gildiia"
        },
        "description": "",
        "slug": "basturma-m-iasna-gildiia",
    }
    output: SizeInfo = parse_weight_info_with_validation(ProductInfo.parse_obj(data14))
    assert output == SizeInfo(value=1.0, unit="кг", type=SizeInfoType.Mass)

    data15 = {
        "normalized_title": "книга обліку boho chic а4 96 аркушів",
        "title": "Книга обліку Buromax Boho Chic А4 96 аркушів",
        "category_id": "book-of-accounts-metro",
        "price": 124.9,
        "weight": "450.0",
        "bundle": 1,
        "weight_info": {
            "value": 450.0,
            "unit": "",
            "type": "quantity"
        },
        "producer": {
            "trademark": "Buromax",
            "trademark_slug": "buromax"
        },
        "description": "",
        "slug": "kniga-obliku",
    }
    output: SizeInfo = parse_weight_info_with_validation(ProductInfo.parse_obj(data15))
    assert output == SizeInfo(value=450.0, unit="г", type=SizeInfoType.Mass)

    data16 = {
        "normalized_title": "шоколад chocolate молочний з молочною начинкою",
        "title": "Шоколад Kinder Chocolate молочний з молочною начинкою 100г",
        "category_id": "block-chocolate-metro",
        "price": 51.9,
        "weight": "100.0",
        "bundle": 1,
        "weight_info": {
            "value": 100.0,
            "unit": "",
            "type": "quantity"
        },
        "producer": {
            "trademark": "Kinder",
            "trademark_slug": "kinder"
        },
        "description": "Молочний шоколад високої якості, створений спеціально для дітей. Завдяки своєму унікальному рецепту – ніжному молочному шоколаду з молочною начинкою – Kinder Chocolate ідеально підходить для дітей, коли їм хочеться солодкого. Мами теж будуть задоволені, адже індивідуально упаковані батончики дають батькам можливість з легкістю контролювати споживання шоколаду дітьми.",
        "slug": "shokolad-kinder-100g",
    }
    output: SizeInfo = parse_weight_info_with_validation(ProductInfo.parse_obj(data16))
    assert output == SizeInfo(value=100.0, unit="г", type=SizeInfoType.Mass)

    data17 = {
        "normalized_title": "шоколад молочний з подрібненими лісовим горіхом",
        "title": "Шоколад молочний Milka з подрібненими лісовим горіхом 6шт 90г",
        "category_id": "block-chocolate-metro",
        "price": 53.98,
        "weight": "92.0",
        "bundle": 1,
        "weight_info": {
            "value": 92.0,
            "unit": "",
            "type": "quantity"
        },
        "producer": {
            "trademark": "Milka",
            "trademark_slug": "milka"
        },
        "description": "Вже понад столiття Мiлка створює найнiжнiший молочний шоколад, використовуючи особливий iнгредiєнт - молоко iз самих Альп! Це молоко дають корiвки, якi по-справжньому насолоджуються життям на справжньому гiрському повiтрi, пишних зелених лугах i теплому сонцi. Цей чарiвний альпiйський свiт допомагає не тiльки створити найнiжнiший шоколад, але й пробудити нiжнiсть у серцi кожного, хто його скуштує. Milka. Найнiжнiший шоколад у свiтi.",
        "slug": "shokolad-milka-90g",
    }
    output: SizeInfo = parse_weight_info_with_validation(ProductInfo.parse_obj(data17))
    assert output == SizeInfo(value=6.0, unit="шт", type=SizeInfoType.Quantity)

    data18 = {
        "normalized_title": "пелюшки tena bed plus сечопоглинаючі",
        "title": "Пелюшки Tena Bed Plus сечопоглинаючі 60x60 30шт",
        "category_id": "adult-diapers-metro",
        "price": 443.88,
        "weight": "1520.0",
        "bundle": 1,
        "unit": "pcs",
        "weight_info": {
            "value": 0.0,
            "unit": "шт",
            "type": "quantity"
        },
        "producer": {
            "trademark": "тена",
            "trademark_slug": "tena"
        },
        "description": "Пелюшки TENA Bed - це пелюшки для захисту поверхонь від випадкових протікань при щоденному догляді або ж для проведення гігієнічних процедур. М'яка поверхня пелюшки приємна для шкіри, а поглинаючий середній і водонепроникний нижній шари забезпечують максимальний захист і гігієну. Кольорове маркування та інформація на зовнішній стороні виробу дозволяють легко визначити продукт. Дерматологічно протестовані.\nХарактеристики:\n-М'яка поверхня\n-Дерматологічно протестовані: безпечні для шкіри.\n-Кольорове маркування на зовнішній стороні.\nДоступні в різних розмірах: 60х60, 60х60, 60х90 і вкладеннях: 5 шт., 30шт.        \nРозмір: 60 х 60 см",
        "slug": "peliushka-tena-polshcha",
        "web_url": "https://metro.zakaz.ua/uk/products/peliushka-tena-polshcha--07322540800746/"
    }
    output: SizeInfo = parse_weight_info_with_validation(ProductInfo.parse_obj(data18))
    assert output == SizeInfo(value=30.0, unit="шт", type=SizeInfoType.Quantity)

    data19 = {
        "normalized_title": "хліб сімейний пшеничний 600 г",
        "title": "Хліб «Київхліб» «Сімейний» пшеничний 600 г",
        "category_id": "497",
        "price": 19.49,
        "weight": "бух",
        "bundle": 0,
        "unit": 0,
        "volume": 0,
        "weight_info": {
            "value": 1.0,
            "unit": "бух",
            "type": "quantity"
        },
        "producer": {
            "trademark": "Київхліб",
            "trademark_slug": 0
        },
        "description": 0,
        "slug": "khlib-kyivkhlib-simeinyi-pshenychnyi-600-g-794354",
    }
    output: SizeInfo = parse_weight_info_with_validation(ProductInfo.parse_obj(data19))
    assert output == SizeInfo(value=600.0, unit="г", type=SizeInfoType.Mass)


    data20 = {
        "normalized_title": "Хліб Metro Chef максі тостовий 10шт х 50г",
        "title": "Хліб Metro Chef максі тостовий 10шт х 50г",
        "category_id": "497",
        "price": 19.49,
        "weight": "бух",
        "bundle": 0,
        "unit": 0,
        "volume": 0,
        "weight_info": {
            "value": 1.0,
            "unit": "бух",
            "type": "quantity"
        },
        "producer": {
            "trademark": "Київхліб",
            "trademark_slug": 0
        },
        "description": 0,
        "slug": "khlib-kyivkhlib-simeinyi-pshenychnyi-600-g-794354",
    }
    output: SizeInfo = parse_weight_info_with_validation(ProductInfo.parse_obj(data20))
    assert output == SizeInfo(value=500.0, unit="г", type=SizeInfoType.Mass)

    data21 = {

        "normalized_title": "хліб шварцвальд на заквасці",
        "title": "Хліб Шварцвальд на заквасці",
        "category_id": "own-bread-and-bakery-products-varus",
        "price": 90.9,
        "weight": "350.0",
        "bundle": 1,
        # "unit": "pcs",
        "weight_info": {
            "value": 350.0,
            "unit": "pcs",
            "type": "quantity"
        },
        "producer": {
            "trademark": "Buromax",
            "trademark_slug": "buromax"
        },
        "description": "",
        "slug": "kniga-obliku"
    }
    output: SizeInfo = parse_weight_info_with_validation(ProductInfo.parse_obj(data21))
    assert output == SizeInfo(value=350.0, unit="г", type=SizeInfoType.Mass)

if __name__ =="__main__":
    test()

