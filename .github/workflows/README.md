# GitHub Actions Workflows

## CI/CD Pipeline

Este repositorio utiliza GitHub Actions para automatizar el proceso de testing y deployment.

## Workflow: `python-app.yml`

### Triggers

El workflow se ejecuta en los siguientes eventos:
- **Push** a las ramas `master` o `main`
- **Pull Requests** hacia las ramas `master` o `main`

### Jobs

#### 1. `test`
- **Ejecuta**: Todos los tests del proyecto
- **Tecnología**: Docker Compose con `docker-compose.test.yml`
- **Validación**: Tests unitarios, de integración, de modelos y endpoints
- **Coverage**: 107 tests cubriendo todas las features

#### 2. `build-and-push`
- **Ejecuta**: Solo en push a `master`/`main` después de tests exitosos
- **Acción**: Build y push de imagen Docker a GitHub Container Registry
- **Tags**: `latest` y SHA específico
- **Repositorio**: `ghcr.io/{owner}/{repo}`

#### 3. `auto-merge` (Nuevo)
- **Ejecuta**: Solo en Pull Requests del mismo repositorio
- **Condición**: Todos los tests deben pasar exitosamente
- **Acción**: Merge automático con método `squash`
- **Seguridad**: Solo PRs del mismo repo (no forks)

### Auto-merge Rules

El auto-merge solo se ejecuta si:

1. ✅ **PR es del mismo repositorio** (no de forks)
2. ✅ **No hay conflictos de merge**
3. ✅ **Todos los tests pasan** (status check `test` = success)
4. ✅ **Permisos adecuados** en el token

### Branch Protection

Para mayor seguridad, se recomienda configurar branch protection rules:

```yaml
# En settings/branches/main
- Require pull request reviews before merging
- Require status checks to pass before merging
  - test (debe pasar)
- Require branches to be up to date before merging
- Do not allow bypassing the above settings
```

### Environment Variables

- `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true` - Forzado para compatibilidad
- `GITHUB_TOKEN` - Automático para operaciones de GitHub
- `github.actor` - Automático para autenticación

### Security Considerations

- **Solo PRs del mismo repo** pueden hacer auto-merge
- **No se procesan forks** automáticamente
- **Tests obligatorios** antes de cualquier merge
- **Permisos mínimos** necesarios para cada job
- **Node.js 24** para seguridad y compatibilidad

### Troubleshooting

#### Auto-merge no funciona:
1. Verificar que el PR sea del mismo repositorio
2. Confirmar que no haya conflictos
3. Verificar que todos los tests pasen
4. Checar permisos del token

#### Tests fallan:
1. Revisar logs del job `test`
2. Verificar `docker-compose.test.yml`
3. Checar dependencias y configuración

#### Build falla:
1. Verificar `Dockerfile.prod`
2. Checar permisos de registry
3. Revisar tags y context

### Monitoreo

Los jobs se pueden monitorear en:
- **Actions tab** del repositorio
- **Pull Request checks**
- **Branch protection status**

### Optimizaciones

- **Cache de Docker** para builds más rápidos
- **Paralelización** de tests si es necesario
- **Matrices** para múltiples entornos
- **Secrets** para credenciales adicionales
