title: Alfred-MailTo Help
author: deanishe@deanishe.net
date: 2013-10-29


Alfred-MailTo Help
==================

![](screenshot-2.png)

**MailTo** is an Alfred 2 Workflow that allows you to send an email to multiple recipients from your Mac Contacts (or your fingers) with the email client of your choice (or just the boring default one).

## Usage ##

To start a new mail without recipients, hit `ENTER` on the `Write new email` result.

To add recipients, type `mailto ` (there's a space at the end there!) and start typing the name or email address of someone in your Contacts or an email address that isn't.

Selecting a result and hitting `TAB` will add that email address to the list of recipients, hitting `ENTER` on a result will add that email address to the list of recipients and open a new email in your selected client (i.e. closing Alfred's window).

## Selecting an email client ##

By default, the Workflow uses your system email client, but you can set any client you want using `mailto setdefault APPNAME` (where `APPNAME` is the name of the application, obviously). It has auto-complete. Note: you're perfectly free to set an app that doesn't send emails, or does, but doesn't support the `mailto:` protocol. If you do that, see <a href="#cleardefault">below</a> to fix it.

To add further recipients, add a comma after the last one and start typing the next name/email address.

## Changing your mind ##

<a name='cleardefault'></a>
If you want to change the email client you've set, you can use `mailto setdefault APPNAME` to set a different one, or `mailto cleardefault` to use your system default email client (which is the default setting).

`mailto getdefault` will show you which email app you have set.

## Technical details ##

The various components that comprise this Workflow use a couple of tricks. Notably, with the official AppleScript access to your Contacts being both broken and *slooooooow*, it tries to find the database files that Contacts/iCloud uses and open them directly for puma-like speed.

This may not always work, but it will always be fast. And I ask you, what self-respecting coder would not favour 1000x faster over correct?

Secondly, the `mailto:` protocol is used to call apps. If an email app doesn't support this protocol, bummer :(

The following apps definitely work:

* Mail.app
* Sparrow
* MailMate
* Unibox
* Google Chrome (if you've [set a handler](https://support.google.com/chrome/answer/1382847?hl=en))

## Copyright etc. ##

All the code I wrote is in the public domain. However, the Workflow also contains the following:

* [alfred.py](https://github.com/nikipore/alfred-python), the author of which has indicated no licensing terms that I'm smart enough to find.
* Email icon from [Icon Archive](http://www.iconarchive.com/show/plex-icons-by-cornmanthe3rd/Communication-email-2-icon.html).
* Original info icon from [IconsDB](http://www.iconsdb.com/royal-blue-icons/info-icon.html).
* Original warning icon also from [IconsDB](http://www.iconsdb.com/orange-icons/warning-icon.html).

## Feedback ##

Mail me at <deanishe@deanishe.net>.