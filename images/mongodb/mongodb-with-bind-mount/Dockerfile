FROM mcr.microsoft.com/mssql/server:2017-latest-ubuntu
ENV ACCEPT_EULA=Y
ENV SA_PASSWORD=eXpress2017
COPY ./data /
ENTRYPOINT [ "/bin/bash", "entrypoint.sh" ]
CMD [ "/opt/mssql/bin/sqlservr" ]