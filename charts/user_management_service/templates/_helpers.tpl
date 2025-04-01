{{- define "user_management_service.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end }}

{{- define "user_management_service.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "user_management_service.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end }}
