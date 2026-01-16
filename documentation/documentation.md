# A comprehensive Guide to the Battlemetrics API


Created by Gnomeslayer

# Table of Contents
- [Introduction](#introduction)
    - [Purpose of this documentation](#purpose-of-this-documentation)
    - [About the Author](#about-the-author)
    - [Assumptions](#assumptions)
- [Installation and setup](#installation-and-setup)
    - [Python Battlemetrics Wrapper](#python-battlemetrics-api-wrapper)
- [Get ban information](#get-ban-information)
- [Delete a ban](#delete-a-ban)

# Introduction

This documentation serves multiple purposes. Primarily, it aims to provide support for users of the Battlemetrics API wrapper, offering clarity on its functionality and usage. Additionally, it fills a crucial gap by offering insights into the Battlemetrics API itself, helping users understand its intricacies and overcome common obstacles.

By documenting both the wrapper and the API, this resource becomes a valuable asset for the gaming community at large. It serves as a centralized reference point where users can find answers to their questions and troubleshoot issues they encounter while interacting with Battlemetrics data.

## Purpose of this documentation
This documentation serves multiple purposes. Primarily, it aims to provide support for users of the Battlemetrics API wrapper, offering clarity on its functionality and usage. Additionally, it fills a crucial gap by offering insights into the Battlemetrics API itself, helping users understand its intricacies and overcome common obstacles.

By documenting both the wrapper and the API, this resource becomes a valuable asset for the gaming community at large. It serves as a centralized reference point where users can find answers to their questions and troubleshoot issues they encounter while interacting with Battlemetrics data.

## About the Author

I am known as Gnomeslayer on Discord and various gaming platforms, and as HaroerHaktak on Reddit. As a dedicated community contributor for Battlemetrics, I am committed to enhancing the user experience through projects like my Python Battlemetrics Wrapper. Additionally, I have collaborated with Cubiquitous to commission a JavaScript/Typescript equivalent, further expanding accessibility to Battlemetrics data across different programming languages.

Through my involvement with Battlemetrics and the development of these wrappers, I bring firsthand expertise and insights to this documentation, ensuring its accuracy and relevance to the community's needs.

With this guide, I aim to empower users with the knowledge and tools they need to unlock the full potential of the Battlemetrics API and its wrappers. Whether you're a seasoned developer or a newcomer to API integration, this resource is designed to support you in achieving your goals effectively and efficiently.

## Assumptions

This guide operates under the assumption that you possess a foundational understanding of programming concepts and methodologies. While we strive to provide clear and concise explanations, it is expected that users have a level of familiarity with programming terminology and practices.

Additionally, we assume that you are proficient in conducting independent research and problem-solving. While we aim to address common challenges and provide solutions, there may be instances where further investigation or experimentation is necessary to fully grasp certain concepts or resolve specific issues. In such cases, we encourage users to leverage online resources and communities for additional guidance.

Furthermore, it is assumed that you have a working knowledge of the programming language relevant to the Battlemetrics API wrapper you are utilizing (e.g., Python or JavaScript/Typescript). Familiarity with basic syntax and data structures within your chosen language will facilitate smoother integration and utilization of the wrapper.

In essence, while this guide endeavors to offer comprehensive support, it does not replace the need for foundational programming skills and self-directed learning. Embracing a proactive and resourceful approach to problem-solving will enhance your experience and proficiency in working with both the Battlemetrics API and its corresponding wrappers.

# Installation and setup

Visit the [Battlemetrics Developers](https://www.battlemetrics.com/developers/documentation) to retrieve a token which will allow you to access the API.

## Python Battlemetrics API Wrapper
You can use `pip install battlemetrics` to install the wrapper or alternatively you can visit the [Github Repo](https://github.com/Gnomeslayer/battlemetrics)
and clone the repo from there.

All endpoints in the wrapper are ASYNC by nature, please take appropriate steps.
```python
from battlemetrics import Battlemetrics

api = Battlemetrics(<your token here>)
```
 
# Get ban information
**RCON ACCESS REQUIRED**<br>
This endpoint retrieves information about a specific ban by it's unique identifier and returns all the relevant information about the ban.
Some examples.
- Ban Reason: Ban Reason
- Ban Note: Notes for staff/Admins
- Relations->User: The (organization) user ID of the person who did it.<br/>

Make a GET request to this URL
`https://api.battlemetrics.com/bans/{banId}`
and the include paramaters are: `server,user,playerIdentifiers,organization,banExemption`

You can view the [Official Battlemetrics Documentation](https://www.battlemetrics.com/developers/documentation#link-GET-ban-/bans/{(%23%2Fdefinitions%2Fban%2Fdefinitions%2Fidentity)}) to read more about this endpoint.

# Wrapper information and example

•	BanID [int] (required): the unique ban identifier for the targeted ban.

## Python Wrapper Example

```
ban_information = asyncio.run(api.bans.info(BanID))
```

## Note

The documentation doesn't tell you everything you can "include" in the request, and the fields don't affect the output.


# Delete a ban
**RCON ACCESS REQUIRED**<br>
This endpoint allows you to delete a targeted ban on a user

Make a POST request to this URL
`https://api.battlemetrics.com/bans/{banId}`

You can view the [Official Battlemetrics Documentation](https://www.battlemetrics.com/developers/documentation#link-DELETE-ban-/bans/{(%23%2Fdefinitions%2Fban%2Fdefinitions%2Fidentity)}) to read more about this endpoint.

# Wrapper information and example

•	BanID [int] (required): the unique ban identifier for the targeted ban.

## Python Wrapper Example

```
ban_information = asyncio.run(api.bans.delete(BanID))
```

## Note

No notes.

# Edit a ban
**RCON ACCESS REQUIRED**<br>
This endpoint allows you to delete a targeted ban on a user

Make a POST request to this URL
`https://api.battlemetrics.com/bans/{banId}`

You can view the [Official Battlemetrics Documentation](https://www.battlemetrics.com/developers/documentation#link-DELETE-ban-/bans/{(%23%2Fdefinitions%2Fban%2Fdefinitions%2Fidentity)}) to read more about this endpoint.

# Wrapper information and example

•	BanID [int] (required): the unique ban identifier for the targeted ban.

## Python Wrapper Example

```
ban_information = asyncio.run(api.bans.delete(BanID))
```

## Note

No notes.