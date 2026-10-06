# ui_difficulty – UI strings of the difficulty settings (draft, owner approval pending)

UI texts (system voice, player addressed with ty; clear, friendly, never jokes; WRITING_METHOD.md rule 7). Existing keys are context only.

## 1. Screens

### PICKER · New Game: difficulty step (title screen → Nová hra → this dialog)

- What: Modal dialog: title, intro, heading, three cards (name + one-line description; Standard preselected and tagged as recommended), buttons Zrušiť / Začať hru. Player addressed with ty.

- `ui.menu.new_game` [existing title-screen button] Nová hra
- `ui.difficulty.pick_title` [dialog title] 
- `ui.difficulty.pick_intro` [intro sentence] 
- `ui.difficulty.title` [heading above the cards] 
- `ui.difficulty.easy` [card name] 
- `ui.difficulty.easy_desc` [card description] 
- `ui.difficulty.standard` [card name] 
- `ui.difficulty.recommended` [tag after the Standard name, lower case: 'Štandardná · odporúčaná'] 
- `ui.difficulty.standard_desc` [card description] 
- `ui.difficulty.hard` [card name] 
- `ui.difficulty.hard_desc` [card description] 
- `ui.common.cancel` [existing button] Zrušiť
- `ui.difficulty.start` [confirm button] 

### SETTINGS · Settings, new first tab

- What: Tab row: Hra, Zvuk, Text a titulky, Obraz, Prístupnosť, Ovládanie. Tab Hra: row 'Obťažnosť' with three choice buttons, the chosen one's description below, then a caption. From the title screen only an explanation.

- `ui.settings.title` [existing screen title] Nastavenia
- `ui.settings.tab_game` [new tab] 
- `ui.settings.tab_audio` [existing tab] Zvuk
- `ui.difficulty.title` [row label] 
- `ui.settings.difficulty_desc` [caption under the choice during a game] 
- `ui.settings.difficulty_menu` [shown instead when settings are opened from the title screen] 

### HINTS · Hint screen (H) per difficulty

- What: Left: quest list. Right: quest title, goal, the caption 'Obťažnosť: Štandardná', revealed hint cards (label + text), then a button or a note. Easy cards are labelled Smer / Postup / Riešenie; Standard: Postrčenie, Kde hľadať; Hard: Postrčenie only, behind a 3-minute countdown (m:ss, e.g. 2:17) that updates every second. HUD tooltip on the hint button while waiting.

- `ui.hint.title` [existing title] Nápoveda
- `ui.hint.next` [existing reveal button] Ďalšia nápoveda
- `ui.hint.show_solution` [existing Easy last-level button] Ukázať presné riešenie
- `ui.hint.level_1` [existing Easy label] Smer
- `ui.hint.level_2` [existing Easy label] Postup
- `ui.hint.level_3` [existing Easy label] Riešenie
- `ui.hint.difficulty` [caption; {difficulty} = Ľahká / Štandardná / Ťažká] 
- `ui.hint.level_nudge` [card label, level 1 on Standard and Hard] 
- `ui.hint.level_where` [card label, level 2 on Standard] 
- `ui.hint.standard_end` [note after both Standard levels] 
- `ui.hint.hard_wait_button` [disabled button while waiting; {time} = 2:17] 
- `ui.hint.hard_wait` [countdown sentence; {time} = 2:17] 
- `ui.hint.hard_wait_note` [rule under the countdown] 
- `ui.hint.hard_end` [note after the Hard nudge] 
- `ui.hint.hard_no_puzzle` [note on a puzzle step on Hard] 
- `ui.hud.hint` [existing HUD button name] Nápoveda
- `ui.hud.hint_wait` [HUD hint button tooltip on Hard while waiting; {time} = 2:17] 
