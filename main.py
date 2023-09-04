#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sug import executor,dp,AlbumMiddleware

if __name__ == '__main__':
    dp.middleware.setup(AlbumMiddleware())
    executor.start_polling(dp, skip_updates=True)



