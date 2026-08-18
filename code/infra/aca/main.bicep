targetScope = 'resourceGroup'

param location string = resourceGroup().location
param prefix string = 'moodframe'
param acrName string
param contentAgentImage string
param imageAgentImage string
param backendImage string
param frontendImage string
@secure()
param githubToken string

resource registry 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' existing = {
  name: acrName
}

resource workspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${prefix}-logs'
  location: location
  properties: {
    retentionInDays: 30
  }
}

resource environment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${prefix}-env'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: workspace.properties.customerId
        sharedKey: workspace.listKeys().primarySharedKey
      }
    }
  }
}

resource pullIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${prefix}-pull'
  location: location
}

resource acrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(registry.id, pullIdentity.id, 'acr-pull')
  scope: registry
  properties: {
    principalId: pullIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '7f951dda-4ed3-4680-a7ca-43fe172d538d'
    )
  }
}

resource contentAgent 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${prefix}-content'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${pullIdentity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: environment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: false
        targetPort: 5001
        transport: 'auto'
        allowInsecure: false
      }
      registries: [{
        server: registry.properties.loginServer
        identity: pullIdentity.id
      }]
      secrets: [{
        name: 'github-token'
        value: githubToken
      }]
    }
    template: {
      containers: [{
        name: 'content-agent'
        image: contentAgentImage
        env: [
          { name: 'GITHUB_TOKEN', secretRef: 'github-token' }
          { name: 'GITHUB_COPILOT_MODEL', value: 'gpt-5.6-sol' }
        ]
        resources: {
          cpu: json('1.0')
          memory: '2Gi'
        }
      }]
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
    }
  }
  dependsOn: [acrPull]
}

resource imageAgent 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${prefix}-image'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${pullIdentity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: environment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: false
        targetPort: 5002
        transport: 'auto'
        allowInsecure: false
      }
      registries: [{
        server: registry.properties.loginServer
        identity: pullIdentity.id
      }]
      secrets: [{
        name: 'github-token'
        value: githubToken
      }]
    }
    template: {
      containers: [{
        name: 'image-agent'
        image: imageAgentImage
        env: [
          { name: 'GITHUB_TOKEN', secretRef: 'github-token' }
          { name: 'GITHUB_COPILOT_MODEL', value: 'gpt-5.6-sol' }
        ]
        resources: {
          cpu: json('1.0')
          memory: '2Gi'
        }
      }]
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
    }
  }
  dependsOn: [acrPull]
}

resource backend 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${prefix}-api'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${pullIdentity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: environment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: false
        targetPort: 8000
        transport: 'auto'
        allowInsecure: false
      }
      registries: [{
        server: registry.properties.loginServer
        identity: pullIdentity.id
      }]
    }
    template: {
      containers: [{
        name: 'backend'
        image: backendImage
        env: [
          { name: 'CONTENT_AGENT_URL', value: 'https://${contentAgent.properties.configuration.ingress.fqdn}' }
          { name: 'IMAGE_AGENT_URL', value: 'https://${imageAgent.properties.configuration.ingress.fqdn}' }
        ]
        resources: {
          cpu: json('0.5')
          memory: '1Gi'
        }
      }]
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
    }
  }
  dependsOn: [acrPull]
}

resource frontend 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${prefix}-web'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${pullIdentity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: environment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 80
        transport: 'auto'
        allowInsecure: false
      }
      registries: [{
        server: registry.properties.loginServer
        identity: pullIdentity.id
      }]
    }
    template: {
      containers: [{
        name: 'frontend'
        image: frontendImage
        env: [
          { name: 'BACKEND_HOST', value: backend.properties.configuration.ingress.fqdn }
          { name: 'BACKEND_SCHEME', value: 'https' }
          { name: 'BACKEND_PORT', value: '' }
        ]
        resources: {
          cpu: json('0.25')
          memory: '0.5Gi'
        }
      }]
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
    }
  }
  dependsOn: [acrPull]
}

output frontendUrl string = 'https://${frontend.properties.configuration.ingress.fqdn}'
output backendUrl string = 'https://${backend.properties.configuration.ingress.fqdn}'
output environmentName string = environment.name
output workspaceName string = workspace.name
