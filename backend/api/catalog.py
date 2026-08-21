def default_catalog_provider() -> dict:
    import openLLV as llv

    return llv.list_available()


def build_catalog(available: dict) -> dict:
    return {
        "algorithms": available.get("algorithms", []),
        "models": available.get("models", []),
        "datasets": available.get("datasets", []),
        "devices": ["auto", "cpu", "mps", "cuda:0"],
        "forms": {
            "enhancement": {
                "traditional_params": {
                    "gamma": {"type": "number", "minimum": 0, "default": 0.6}
                }
            },
            "training": {
                "epochs": {"type": "integer", "minimum": 1},
                "batch_size": {"type": "integer", "minimum": 1},
                "lr": {"type": "number", "exclusiveMinimum": 0},
            },
        },
    }


def catalog_names(available: dict, category: str) -> set[str]:
    names = set()
    for item in available.get(category, []):
        names.add(item["name"].casefold())
        names.update(alias.casefold() for alias in item.get("aliases", []))
    return names
