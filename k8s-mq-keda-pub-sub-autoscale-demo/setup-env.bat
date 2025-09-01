@echo off
set KUBECONFIG=%USERPROFILE%\.kube\config
set KEDA_NAMESPACE=keda-system
set RABBITMQ_NAMESPACE=rabbitmq-demo
echo Environment variables set for RabbitMQ KEDA Demo
echo KUBECONFIG: %KUBECONFIG%
echo KEDA_NAMESPACE: %KEDA_NAMESPACE%
echo RABBITMQ_NAMESPACE: %RABBITMQ_NAMESPACE%
echo.
echo Checking cluster status...
kubectl get pods -n %KEDA_NAMESPACE%
kubectl get pods -n %RABBITMQ_NAMESPACE%
echo.
echo RabbitMQ Management UI: http://localhost:31672 (admin/admin123)
echo AMQP Connection: localhost:30672