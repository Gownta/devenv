# VSCode config
---------------

Extensions:
- Vim, so that I have vim bindings

Settings:
- terminal.integrated.fontFamily: NotoMono Nerd Font
- terminal.integrated.fontSize: 16

I cannot override cmd+backtick using the regular keybinding setup, since that is a mac builtin, so it needs to be overridden in the keybinding JSON.
cmd shift p > Preferences: Open Keyboard Shortcuts (JSON) >
```
{
	"key": "cmd+`",
	"command": "workbench.action.terminal.toggleTerminal"
}
```
