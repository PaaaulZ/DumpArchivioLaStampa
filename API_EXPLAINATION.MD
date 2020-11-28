# www.archiviolastampa.it "API" reversing.

I don't have official names so I'll make my own.

## ID explaination

Every page in the archive has an ID made like this: **[aaaa]_[bb]_[cccc]_[dddd]_[eeee]_[ffffffff]** (Ex: **1282_01_1867_0001_0001_18769495**).

- [aaaa] seems fixed to 1282 until a certain year. (???)
- [bb] is the newspaper id. Seems fixed to 01 => "La Stampa". (???)
- [cccc] is the publication year, starts from 1867 and ends in 2005.
- [dddd] is the edition number of that year.
- [eeee] is the page number.
- [ffffffff] is the metadata id, i think. It's used for another API to download metadata (text coordinates and ocr text)

**Always pad the fields with zeros to reach the correct length!**

## Prerequisites

To interact with every page you'll need and "s_field" (?s= in the GET requests) and some cookies.

s_field comes from an HTML field in every page (or at least in the home page)

```
<input type="hidden" name="t" value="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" />
```

You can get the cookies you need (mainly SESSION IDS) just from visiting the homepage.
You're going to have something like this

```
"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx=yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy; mosvisitor=1; PHPSESSID=aaaaaaaaaaaaaaaaaaaaaaaaaa; JSESSIONID=zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz.instanceNNN"
```

**FOR EVERY API CALL YOU WILL NEED TO PASS THE COOKIES OR YOU WILL GET ERROR 501**

## How can we loop?

- For each edition we call the "Edition details" API that gives us and "edition number" and "edition year".
- We call the "Pages" API that gives us an array with the id of every single page of that edition.
- We download every page of that edition (using the "Download" API)
- We call the "Neighbours" API to get the next edition id and start over!

We start with the first edition id (I got it for you from the homepage since start and end are known and hardcoded in the script)!


## API list and explaination


### "Edition details" API

Input: page_id => Publication id (the **[aaaa]_[bb]_[cccc]_[dddd]_[eeee]_[ffffffff]** one). "Page" and "Metadata ID" are not important here.

Output: A JSON formatted array with edition number and edition date. Fields are called "uscita" and "data_uscita".

URL:

```
http://www.archiviolastampa.it/index2.php?option=com_lastampa&task=issue&no_html=1&type=info&issueid={PAGE_ID}
```

### "Pages" API

Input: page_id => Publication id (the **[aaaa]_[bb]_[cccc]_[dddd]_[eeee]_[ffffffff]** one). "Page" and "Metadata ID" are not important here.

Input: s_field => The s_field we got from the start.

Output: A JSON formatted array with the ID of every page of that edition!. Fields are called "number" and "thumbnailId".

```
http://www.archiviolastampa.it/load.php?url=/item/getPagesInfo.do?id={PAGE_ID}&s={S_FIELD}
```

### Neighbours API

Input: edition_date => A YYYY-MM-DD HH:mm:ss formatted date

Output: Previous and Next edition IDs and date. ID Fields are called "previousIssueId" and "nextIssueId".

```
http://www.archiviolastampa.it/index2.php?option=com_lastampa&task=issue&no_html=1&type=neighbors&headboard=01&date={EDITION_DATE}
```

### "Download" API

Input: page_id => Publication id (the **[aaaa]_[bb]_[cccc]_[dddd]_[eeee]_[ffffffff]** one). "Page" IS IMPORTANT here, obviously.

Input: s_field => The s_field we got from the start.

Output: a JPG image you can directly save to a file.

```
http://www.archiviolastampa.it/load.php?url=/downloadContent.do?id={PAGE_ID}&s={S_FIELD}
```

