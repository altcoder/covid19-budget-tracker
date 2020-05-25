#!/usr/bin/env bash

# Decrypt the token files used for Github Workflows CI

# --batch to prevent interactive command
# --yes to assume "yes" for questions
gpg --quiet --batch --yes --decrypt --passphrase="$TOKEN_PASSPHRASE" --output $GITHUB_WORKSPACE/credentials/g_oauth_clt.pickle $GITHUB_WORKSPACE/config/tokens/g_oauth_clt.pickle.gpg
