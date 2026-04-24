from app.schemas.rule_models import MergeGuardConfig


class RulesLoader:
    def load(self, raw_config: dict) -> MergeGuardConfig:
        if "merge_guard" in raw_config and isinstance(raw_config["merge_guard"], dict):
            raw_config = raw_config["merge_guard"]
        return MergeGuardConfig.model_validate(raw_config or {})