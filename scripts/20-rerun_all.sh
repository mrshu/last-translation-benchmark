# correct order in which to run the scripts
python3 scripts/02-fresh_data.py
python3 scripts/20a-synthetic_verification_rules.py
python3 scripts/20b-translate_by_extra_models.py
python3 scripts/20c-verify_by_extra_models.py
python3 scripts/20c-verify_by_extra_models.py --no-cache --chunks 100
python3 scripts/20d-annotate_linguistics.py