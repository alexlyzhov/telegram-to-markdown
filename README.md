# Convert exported Telegram messages to Markdown journals

Do you have an unruly collection of notes you have sent to yourself as Telegram messages and want to have more control over it and greater privacy?  
Or do you want to export your message history with someone in such a way that you could edit it easily?  
This script may be useful.

It takes a JSON record of your Telegram message history along with all the attachments as input.
An output is a collection of chronologically organised Markdown files, each file storing all the messages on a given date.

## Usage

- Export all your Telegram data in JSON

- `pip install -r requirements.txt`

- `python convert.py convert <input_dir> <output_dir> [<tag1> <tag2> ...]`, e.g. `python convert.py convert DataExport_2022-01-12 vault`
where `<input_dir>` is the root folder of your Telegram export and `<output_dir>` is the name of the new directory with outputs.  
The optional tag arguments in the end of the command is a whitelist of tags to preserve: I've found it helpful to escape the hashtag signs in Telegram messages in all instances outside of a few selected hashtags which I actually use.

- The results in `<output_dir>` are structured with `journals` and `assets` directories which is compatible with both Logseq and Obsidian. `<output_dir>` can be opened directly as a Logseq graph or an Obsidian vault.
You may just have to change the date format in settings if it doesn't match the filename format in `journals`.

## Smaller details

This works very well for me but since it was tested on a limited set of messages, it may not process all the rare details of the message entry schema perfectly, especially after it would be changed by Telegram again.

The script pulls the messages from the "Saved messages" chat (although it isn't a problem to modify it to pull messages from some other chat).

`*` and `_` characters in message text are escaped and do not cause formatting to change (unless the text is explicitly marked as e.g. bold or italic in JSON).
Characters responsible for additional formatting in the Obsidian-flavored markown such as `~` and `$` are all escaped as well.
Hashtag signs are escaped unless the hashtag is in the whitelist.
