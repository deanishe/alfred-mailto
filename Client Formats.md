title: Client Formats
author: deanishe@deanishe.net
date: 2013-12-05

# Client Formats #

The mailto: URL format required by various clients.

| Key |               |
| --- | ------------- |
| YES | required      |
| NO  | breaks things |
| -   | doesn't care  |


|    Client   | Spaces | Mime-encoded | Email only | URL-quoted |
|-------------|--------|--------------|------------|------------|
| Mail.app    | -      | -            | -          | -          |
| Airmail     | NO     |              | YES        |            |
| Unibox      | -      | NO           | -          | NO         |
| Sparrow     | -      | -            | -          | NO         |
| MailMate    | YES    | -            | -          | -          |
| ThunderBird | -      | NO           | -          | -          |
| Mailbox     | NO     | NO           | YES        | NO         |

Mail.app
: Works with or without MIME-encoding and URL-quoting. MIME-encoding requires URL-quoting.

Airmail
: Email addresses only, no spaces.

Unibox
: Email-only for contacts with commas in the name. Diacritics, non-ascii fine.

Sparrow
: Works fine except with URL-quoting.

MailMate
: Must have spaces.

ThunderBird
: No MIME-encoding.

Mailbox (Beta)
: Email addresses only, no spaces.

## Preferred formats ##

|                    Format                   |                       Clients                        |
|---------------------------------------------|------------------------------------------------------|
| Standard (spaces, MIME-encoded, URL-quoted) | Mail.app, MailMate, Thunderbird                      |
| Email-only, no spaces                       | Airmail, Mailbox (Beta)                              |
| Email-only for contacts with commas         | Unibox                                               |
| Only add quotes to names with commas        | Sparrow, Google Chrome (also works with first group) |
|                                             |                                                      |

MIME-encoding, URL-quoting never necessary.