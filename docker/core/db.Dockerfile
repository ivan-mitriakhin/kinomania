FROM postgres:17.0

RUN apt-get update -y && \
    apt-get install -y curl && \
    apt-get install -y unzip

RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    ./aws/install

RUN aws s3 cp s3://kinomania/kinomania.sql ./ --no-sign-request