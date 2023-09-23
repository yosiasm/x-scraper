Scraper to get 100 tweet from public user

### How to get AUTH TOKEN?
1. open your x in a browser
2. run your devtools
3. find a request from https://twitter.com/i/api/graphql (UserTweets?variables=....)
4. check the header tab
5. the token is in Authorization field
6. modify script, paste token you got in AUTH TOKEN

### How to use?
```python scraper.py account1 account2 account3```