
# Client Formats #

The mailto: URL format required by various clients.

| Key |               |
| --- | ------------- |
| YES | required      |
| NO  | breaks things |
| -   | doesn't care  |


|     Client     | Spaces | Mime-encoded | Email only | URL-quoted | Commas | "Inline to" |
|----------------|--------|--------------|------------|------------|--------|-------------|
| Mail.app       | -      | -            | -          | -          | -      | -           |
| Airmail 1      | -      | NO           | YES        |            |        | YES         |
| Unibox         | -      | NO           | -          | NO         | NO     | -           |
| Sparrow        | -      | -            | -          | NO         | -      | -           |
| MailMate       | YES    | -            | -          | -          | -      | -           |
| ThunderBird    | -      | NO           | -          | -          | -      | -           |
| Mailbox (Beta) | NO     | NO           | -          | NO         | NO     | NO          |


Mail.app
: Works with or without MIME-encoding and URL-quoting. MIME-encoding requires URL-quoting.

Airmail
: Email addresses only, no spaces. Requires "inline to".

Unibox
: Email-only for contacts with commas in the name. Diacritics, non-ascii fine.

Sparrow
: Works fine except with URL-quoting.

MailMate
: Must have spaces.

ThunderBird
: No MIME-encoding.

Mailbox (Beta)
: Commas in names break everything. Quoting doesn't help. Requires "separate to".

## Preferred formats ##

|                Format                |                       Clients                        |
|--------------------------------------|------------------------------------------------------|
| Standard (spaces, name and email)    | Mail.app, MailMate, Thunderbird                      |
| Email-only, no spaces, "inline to"   | Airmail                                              |
| Email-only for contacts with commas  | Unibox, Mailbox (Beta)                               |
| Only add quotes to names with commas | Sparrow, Google Chrome (also works with first group) |
|                                      |                                                      |

MIME-encoding, URL-quoting never necessary.

## Inline/separate to ##

Airmail requires a URI of format `mailto:email.address@domain.com`,
Mailbox (Beta) requires a URI of format `mailto:?to=email.address@domain.com`
(for names to work at all). Everything else doesn't care.
