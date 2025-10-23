"""
Make my VSCode keybindings

Paste the output of this script into my keybindings.json override:
  VSCode > cmd + shift + p
"""

import json

bindings = {}
bindings["cmd+`"] = "workbench.action.terminal.toggleTerminal"

for i in range(1, 10):
    bindings[f"cmd+{i}"] = f"workbench.action.openEditorAtIndex{i}"

bindings["ctrl+1"] = "workbench.action.focusFirstEditorGroup"
bindings["ctrl+2"] = "workbench.action.focusSecondEditorGroup"
bindings["ctrl+3"] = "workbench.action.focusThirdEditorGroup"
bindings["ctrl+4"] = "workbench.action.focusFourthEditorGroup"
bindings["ctrl+5"] = "workbench.action.focusFifthEditorGroup"
bindings["ctrl+6"] = "workbench.action.focusSixthEditorGroup"
bindings["ctrl+7"] = "workbench.action.focusSeventhEditorGroup"
bindings["ctrl+8"] = "workbench.action.focusEighthEditorGroup"

bindings["ctrl+9"] = "workbench.action.lastEditorGroup"

j = [{"key": k, "command": v} for k, v in bindings.items()]
print(json.dumps(j, indent = 4))
