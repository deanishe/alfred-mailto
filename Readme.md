
Alfred-MailTo
=============

![](img/screenshot-2.png)

A Workflow for [Alfred 2](http://www.alfredapp.com/) that allows you to choose recipients from your Mac Contacts, including Groups (or enter email addresses manually) and compose a message using the email app of your choice.

Uses the [alfred-python](https://github.com/nikipore/alfred-python) library by [nikipore](https://github.com/nikipore) and [docopt](http://docopt.org/).

## Usage ##

Open Alfred, type `mailto` (the default keyword) then either hit `ENTER` to open an entirely blank message or start typing the name or email address you'd like to send a mail to.

Addresses will be suggested from matching contacts and groups in your Mac address book. Hit `TAB` to autocomplete the recipient list from the selected result, or `ENTER` or `⌘+NUM` to add the address and start composing a mail.

You can add multiple recipients by adding a comma between them.

## Supported applications ##

The Workflow uses the `mailto:` protocol and as such should work with pretty much any email client.

The following apps definitely work:

* Mail.app
* Sparrow
* MailMate
* Unibox
* Airmail
* Thunderbird
* Google Chrome (if you've [set a handler](https://support.google.com/chrome/answer/1382847?hl=en))

The following do **not** work:

* Safari (it will open your default mail client instead)

## Copyright, licensing etc. ##

* All the code I wrote is released under the [MIT licence](http://opensource.org/licenses/MIT).
* [alfred.py](https://github.com/nikipore/alfred-python)'s author has indicated no licensing terms that I'm smart enough to find.
* [docopt](http://docopt.org/) is released under the [MIT licence](http://opensource.org/licenses/MIT).
* Email icon from [Icon Archive](http://www.iconarchive.com/show/plex-icons-by-cornmanthe3rd/Communication-email-2-icon.html) is free for personal use.
* Original info icon from [IconsDB](http://www.iconsdb.com/royal-blue-icons/info-icon.html) is CC0 1.0 public domain.
* Original warning icon also from [IconsDB](http://www.iconsdb.com/orange-icons/warning-icon.html) as above.

## Screenshots ##

Create an empty message:

![](img/screenshot-1.png "Create an empty message")

Auto-complete addresses from your Contacts by name or by email address:

![](img/screenshot-2.png "Auto-complete from your address book by name")

![](img/screenshot-3.png "Auto-complete from your address book by email address")

Add multiple recipients:

![](img/screenshot-4.png "Add multiple recipients")

Handle unknown recipients and invalid addresses intelligently:

![](img/screenshot-5.png "Enter recipients manually")

![](img/screenshot-6.png "No mails to invalid addresses")

![](img/screenshot-7.png "Mail only valid addresses")

## Further information ##

For more information, please see the included help file. `mailto help` will open it from within Alfred.