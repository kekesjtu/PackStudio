from packstudio.domain.materials import Material
from packstudio.templates.package_library.core.materials import make_material


def materials_for(template_id: str) -> list[Material]:
    return {
        "fbga_fsbga": _fbga(),
        "wirebond_pbga": _wirebond_pbga(),
        "qfn": _qfn(),
        "qfp_family": _qfp(),
        "soic_family": _soic(),
    }.get(template_id, [])


def _fbga() -> list[Material]:
    return [
        make_material("fbga-trace-top", "Trace0", 77.16, 3306, 631.4367816091953, "#C46A32"),
        make_material(
            "fbga-trace-bottom",
            "Trace1",
            38.68,
            2603,
            737.1167883211679,
            "#B96331",
        ),
        make_material(
            "fbga-via",
            "Via",
            168.45218125,
            3907.5282875,
            385.1039902452658,
            "#C46A32",
        ),
        make_material(
            "fbga-bondwire-x",
            "bondwire1",
            (30.8810137518925, 0.68, 30.8810137518925),
            3607.598944816067,
            471.6740510924182,
            "#D9A928",
        ),
        make_material(
            "fbga-bondwire-y",
            "bondwire2",
            (0.68, 30.8810137518925, 30.8810137518925),
            3607.598944816067,
            471.6740510924182,
            "#D9A928",
        ),
    ]


def _wirebond_pbga() -> list[Material]:
    return [
        make_material(
            "wirebond-trace-top",
            "Trace0",
            115.64,
            4009,
            562.8199052132702,
            "#C46A32",
        ),
        make_material(
            "wirebond-trace-bottom",
            "Trace5",
            38.68,
            2603,
            737.1167883211679,
            "#B96331",
        ),
        make_material(
            "wirebond-die-flag",
            "die_flag",
            231.08,
            6118,
            451.583850931677,
            "#B96331",
        ),
        make_material(
            "wirebond-via",
            "Via",
            138.6,
            3214.8,
            385,
            "#C46A32",
        ),
        make_material(
            "wirebond-bondwire-x",
            "bondwire_1",
            (47.4553300989311, 0.68, 47.4553300989311),
            4588.633245731125,
            382.3576684058402,
            "#D9A928",
        ),
        make_material(
            "wirebond-bondwire-y",
            "bondwire_2",
            (0.68, 47.4553300989311, 47.4553300989311),
            4588.633245731125,
            382.3576684058402,
            "#D9A928",
        ),
    ]


def _qfn() -> list[Material]:
    return [
        make_material(
            "qfn-bondwire-x",
            "bondwire-x",
            (18.6187785190195, 0.88, 18.6187785190195),
            3049.250069781266,
            50.8380029316774,
            "#D9A928",
        ),
        make_material(
            "qfn-bondwire-y",
            "bondwire-y",
            (0.88, 18.6187785190195, 18.6187785190195),
            3049.250069781266,
            50.8380029316774,
            "#D9A928",
        ),
    ]


def _qfp() -> list[Material]:
    return [
        make_material(
            "qfp-leadframe-inner-x",
            "LeadFrame_1x",
            (151.09, 0.68, 151.09),
            5360,
            469.3787313432836,
            "#B96331",
        ),
        make_material(
            "qfp-leadframe-inner-y",
            "LeadFrame_1y",
            (0.68, 151.09, 151.09),
            5360,
            469.3787313432836,
            "#B96331",
        ),
        make_material(
            "qfp-leadframe-outer-x",
            "LeadFrame_2x",
            (150.76305, 0.0261, 150.76305),
            4450.5807,
            385.0811569150966,
            "#B96331",
        ),
        make_material(
            "qfp-leadframe-outer-y",
            "LeadFrame_2y",
            (0.0261, 150.76305, 150.76305),
            4450.5807,
            385.0811569150966,
            "#B96331",
        ),
        make_material(
            "qfp-bondwire-x",
            "bondwire1",
            (54.8883051392426, 0.68, 54.8883051392426),
            5028.591269924019,
            353.6214185791503,
            "#D9A928",
        ),
        make_material(
            "qfp-bondwire-y",
            "bondwire2",
            (0.68, 54.8883051392426, 54.8883051392426),
            5028.591269924019,
            353.6214185791503,
            "#D9A928",
        ),
        make_material("qfp-die-flag", "die_flag", 180.9, 6068, 444.6268951878708, "#B96331"),
        make_material(
            "qfp-tie-bar",
            "tie_bar",
            (106.596347263872, 106.596347263872, 0.68),
            8900,
            385,
            "#B96331",
        ),
    ]


def _soic() -> list[Material]:
    return [
        make_material(
            "soic-leadframe-inner",
            "LeadFrame_1",
            83.3004724409449,
            4018.425196850394,
            274.3423599952972,
            "#B96331",
        ),
        make_material(
            "soic-leadframe-outer",
            "LeadFrame_2",
            82.8525251968504,
            2772.449148031496,
            1.2886900029616,
            "#B96331",
        ),
        make_material(
            "soic-bondwire-x",
            "bondwire1",
            (11.2952762294981, 0.68, 11.2952762294981),
            2448.318530717958,
            669.4852429942155,
            "#D9A928",
        ),
        make_material(
            "soic-bondwire-y",
            "bondwire2",
            (0.68, 11.2952762294981, 11.2952762294981),
            2448.318530717958,
            669.4852429942155,
            "#D9A928",
        ),
        make_material("soic-die-flag", "die_flag", 157.8, 6008, 107.7523302263649, "#B96331"),
    ]
