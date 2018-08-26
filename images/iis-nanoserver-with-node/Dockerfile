#FROM microsoft/dotnet:2.1-sdk
FROM microsoft/iis:nanoserver
ENV node_version_name="node-v8.11.4-win-x64"
ENV node_file_name="$node_version_name.zip"
ENV node_download_url="https://nodejs.org/dist/v8.11.4/$node_file_name"

# setup powershell options for RUN commands
SHELL ["powershell", "-Command", "$ErrorActionPreference = 'Stop';$ProgressPreference = 'Continue';"]

# download and extract node, and remove zip file when done
RUN MKDIR "c:\\node"
RUN Invoke-WebRequest -Uri $env:node_download_url -OutFile "c:\\node\\$env:node_file_name";
RUN Expand-Archive -Path "c:\\node\\$env:node_file_name" -DestinationPath "c:\\node"
RUN Remove-Item -Force "c:\\node\\$env:node_file_name"

#set node/npm path permanantly
RUN $NewLocation = \"C:\\node\\$env:node_version_name\"; \
	Write-Host \"=> New folder location: '$NewLocation'\"; \
	$Reg = \"Registry::HKLM\System\CurrentControlSet\Control\Session Manager\Environment\"; \
	Write-Host \"=> Reg. Path: '$Reg'\"; \
	$OldPath = (Get-ItemProperty -Path \"$Reg\" -Name PATH).Path; \
	Write-Host \"=> Old Path: '$OldPath'\"; \
	$NewPath= \"$OldPath;$NewLocation\"; \
	Write-Host \"=> New Path: '$NewPath'\"; \
	Set-ItemProperty -Path \"$Reg\" -Name PATH –Value $NewPath

ENV ASPNETCORE_URLS="http://0.0.0.0:80"
