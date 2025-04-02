{{- define "user-management-service.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end }}

{{- define "user-management-service.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "user-management-service.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end }}
