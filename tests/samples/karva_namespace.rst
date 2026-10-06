>>> assert fresh == []
>>> fresh.append("value"); shared.append("value"); counter += 1
>>> assert shared == ["value"]; assert counter == 1; counter += 2
