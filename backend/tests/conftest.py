import os


# Unit/integration tests are deterministic and must never spend external API quota.
os.environ["LLM_ENABLED"] = "false"
