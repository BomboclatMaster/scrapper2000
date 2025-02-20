# **Azure Pipeline Agent and Azure Environment Agent Setup Guide**

## **1. Prerequisites**
Before setting up agents, ensure the following:

✅ **Azure DevOps Organization** is created.  
✅ **Administrator access** on the machine(s) where the agent will be installed.  
✅ **Internet access** is available to connect the agent to Azure DevOps.  
✅ **Personal Access Token (PAT)** is generated for authentication.

---

## **2. Understanding Agent Types**
In **Azure DevOps**, you may need:
- **Pipeline Agents** → For running CI/CD pipelines.
- **Environment Agents** → For handling deployments in **Staging, Production**, etc.

You can set up:
- **Shared agents** → Used by multiple projects or environments.
- **Project-specific agents** → Dedicated to a single project or environment.

---

## **3. Naming Conventions for Agents**
### **Agent Pool Naming (Pipeline Agents)**
| Scenario | Suggested Naming |
|----------|----------------|
| Shared agent pool for all projects | `Shared-Pipeline-Pool` |
| Dedicated pool for a specific project | `{ProjectName}-Pipeline-Pool` |
| Department-specific pool | `{DepartmentName}-Pipeline-Pool` |

**Examples:**  
- `Shared-Pipeline-Pool`
- `App1-Pipeline-Pool`
- `Finance-Pipeline-Pool`

### **Pipeline Agent Naming**
| Scenario | Suggested Naming |
|----------|----------------|
| Shared agent running multiple pipelines | `Pipeline-Agent-{Number}` |
| Dedicated agent for a specific project | `{ProjectName}-Pipeline-Agent-{Number}` |
| Agent running on a specific server | `{ServerName}-Agent-{Number}` |

**Examples:**  
- `Pipeline-Agent-01`
- `App1-Pipeline-Agent-02`
- `CI-Server1-Agent-03`

### **Environment Naming (Deployment Agents)**
| Scenario | Suggested Naming |
|----------|----------------|
| Shared environment for all projects | `Shared-{EnvironmentName}` |
| Dedicated environment for a specific project | `{ProjectName}-{EnvironmentName}` |

**Examples:**  
- `Shared-Staging`
- `App1-Production`
- `Finance-QA`

### **Environment Agent Naming**
| Scenario | Suggested Naming |
|----------|----------------|
| General environment agent | `{EnvironmentName}-Env-Agent-{Number}` |
| Dedicated agent for a project environment | `{ProjectName}-{EnvironmentName}-Agent-{Number}` |

**Examples:**  
- `Staging-Env-Agent-01`
- `App1-Production-Agent-02`
- `Finance-QA-Agent-03`

---

## **4. Setting Up an Azure Pipeline Agent**
### **Step 1: Create an Agent Pool**
1. **Go to Azure DevOps** → `https://dev.azure.com/{your-organization}`
2. Open **Organization Settings** → **Agent Pools** under **Pipelines**.
3. Click **Add pool**.
4. Provide a **name** (e.g., `App1-Pipeline-Pool`).
5. Choose **Self-hosted**.
6. Click **Create**.

---

### **Step 2: Install and Configure the Agent**
1. **Download the Agent Package**  
   - Go to **Azure DevOps → Agent Pools**.  
   - Select the pool (`App1-Pipeline-Pool`).  
   - Click **New Agent** → Choose OS (Windows/Linux/macOS) → **Download**.

2. **Extract the Agent Package**
   ```sh
   mkdir /opt/azure-agent-app1
   cd /opt/azure-agent-app1
   tar zxvf ~/downloads/vsts-agent-linux-x64.tar.gz
   ```

3. **Configure the Agent**
   ```sh
   ./config.sh
   ```
   - **Enter Azure DevOps URL**: `https://dev.azure.com/{your-organization}`
   - **Choose authentication**: `PAT (Personal Access Token)`
   - **Enter the PAT**
   - **Select the Agent Pool**: `App1-Pipeline-Pool`
   - **Agent Name**: `App1-Pipeline-Agent-01`
   - **Work Directory**: Default (`_work`)

4. **Run the Agent as a Service**
   ```sh
   sudo ./svc.sh install
   sudo ./svc.sh start
   ```

---

## **5. Setting Up an Azure Environment Agent**
### **Step 1: Create an Environment**
1. **Go to Azure DevOps → Pipelines → Environments**.
2. Click **New Environment**.
3. Provide a **name** (e.g., `Staging`, `Production`).
4. Click **Create**.

---

### **Step 2: Install and Register the Environment Agent**
1. **Add Deployment Target**
   - Inside the environment (`Staging`), click **Add Resource** → **Virtual Machine**.
   - Copy the **provided registration script**.

2. **Run the Registration Script on the Deployment VM**
   ```sh
   curl -fsSL https://raw.githubusercontent.com/microsoft/azure-pipelines-agent/main/scripts/install.sh | bash
   ```
   - Enter **Azure DevOps details**.

3. **Configure Each Environment Agent**
   ```sh
   cd /opt/azure-env-staging
   ./config.sh
   ```
   - Select **Staging** environment.

   ```sh
   cd /opt/azure-env-production
   ./config.sh
   ```
   - Select **Production** environment.

4. **Run the Agent as a Service**
   ```sh
   sudo ./svc.sh install
   sudo ./svc.sh start
   ```

---

## **6. Using Agents in Azure Pipelines**
### **Pipeline Agent Usage**
```yaml
pool:
  name: App1-Pipeline-Pool  
steps:
  - script: echo "Running CI/CD for App1"
```

### **Environment Agent Usage**
```yaml
stages:
- stage: DeployToStaging
  jobs:
  - deployment: StagingDeploy
    environment: Staging
    strategy:
      runOnce:
        deploy:
          steps:
            - script: echo "Deploying to Staging"

- stage: DeployToProduction
  jobs:
  - deployment: ProductionDeploy
    environment: Production
    strategy:
      runOnce:
        deploy:
          steps:
            - script: echo "Deploying to Production"
```

---

## **7. Managing and Scaling Agents**
- **Adding More Agents** → Install a new agent and configure it with the same pool.
- **Load Balancing** → Azure Pipelines distributes jobs across available agents.
- **Monitoring Agents** → Go to **Azure DevOps → Agent Pools** and check logs.

---

## **8. Troubleshooting**
### **Agent Not Appearing in Azure DevOps**
```sh
./svc.sh status
```
- Restart the agent:
  ```sh
  ./svc.sh restart
  ```

### **Agent Connectivity Issues**
- Ensure outbound connections to `dev.azure.com` are allowed.
- Regenerate and update the **Personal Access Token (PAT)** if authentication fails.

---

## **9. Conclusion**
✅ Successfully set up **pipeline agents** for CI/CD.  
✅ Configured **environment agents** for deployment.  
✅ Standardized **naming conventions** for easy management.  

🚀 Your Azure DevOps agents are now ready to run builds and deployments efficiently!

