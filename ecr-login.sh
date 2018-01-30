#!/bin/bash

# need to upgrade awscli to >= awscli-1.12.2
login=`aws ecr get-login --no-include-email --region us-west-2`
exec ${login}
