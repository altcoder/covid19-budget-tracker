#!/usr/bin/env bash

gpg --symmetric --cipher-algo AES256 credentials/g_oauth_clt.pickle
mv credentials/g_oauth_clt.pickle.gpg config/tokens/g_oauth_clt.pickle.gpg
