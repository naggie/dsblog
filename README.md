DSBLOG, the Darksky Blog Aggregator
===================================

DSBLOG aggregates articles and user profiles from the following sources:

 1. A discourse blog category
 2. A ghost blog
 3. Static YAML files

 In the defined order of precedence.



## DSBlog crawler POC article spec:

Includes image

 * title
 * url: original URL
 * content: html content with full qualified URLs/Images (including protocol)
 * ...

## DSBlog crawler article spec:
 * user_email (ID of user, used to populate image and name later)
 * no author_image,author_name,author_url

## DSBlog renderable article spec:
Same as POC crawler article spec, but
 * Image URLs are localised
 * image is 710x100 header image (rectange fit in center, scaled, of first or chosen image

## DSBlog user spec:

Users are identified by email address alone. A user object has the following attributes:

  * name: full name
  * email
  * bio: HTML bio
  * avatar: a square image URL (200x200 or more preferred)
  * website
