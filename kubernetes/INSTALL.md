```sh
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

kubectl create namespace ingress-nginx

helm install ingress-nginx ingress-nginx/ingress-nginx \
--namespace ingress-nginx \
--set controller.metrics.enabled=true \
--set-string controller.podAnnotations."prometheus\.io/scrape"="true" \
--set-string controller.podAnnotations."prometheus\.io/port"="10254"
```

```sh
kubectl get services -n ingress-nginx
```

```sh
kubectl apply --kustomize github.com/kubernetes/ingress-nginx/deploy/prometheus/
```

```sh
kubectl create namespace keda

helm repo add kedacore https://kedacore.github.io/charts
helm repo update

helm install keda kedacore/keda --version 2.3.0 --namespace keda
```

```sh
kubectl apply -f kubernetes/deployment.yaml -n ingress-nginx
kubectl apply -f kubernetes/service.yaml -n ingress-nginx
```

```sh
kubectl apply -f kubernetes/ingress.yaml -n ingress-nginx
```

```sh
kubectl apply -f kubernetes/scaled-object.yaml -n ingress-nginx
```

