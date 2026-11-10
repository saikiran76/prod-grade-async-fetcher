# Production Grade Asynchronous crawler

## Semaphore commit reference (analyzing coroutine sequence)
![alt text](semaphore_permit_allocation.png)
### reference output testing out semaphore permits for coroutines
```
--bash--
(.venv) PS E:\projects\prod-async-fetcher> python src/prod_async_fetcher/main.py
maximum reqs at this point:  2
maximum reqs at this point:  2
maximum reqs at this point:  2
maximum reqs at this point:  2
maximum reqs at this point:  2
responses:  [<Response [200 OK]>, <Response [200 OK]>, <Response [200 OK]>, <Response [403 Forbidden]>, <Response [301 Moved Permanently]>]
Close inside context:  False
closed after context:  True
fetcher client after context:  None
```
