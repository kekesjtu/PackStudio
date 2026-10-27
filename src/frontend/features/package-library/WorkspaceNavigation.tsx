import List from '@mui/material/List'
import ListItemButton from '@mui/material/ListItemButton'
import ListItemText from '@mui/material/ListItemText'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import { Fragment } from 'react'

import type { TemplateSchema } from './types'

interface WorkspaceNavigationProps {
  schema: TemplateSchema
  activeStep: string
  onSelect: (stepId: string) => void
}

export default function WorkspaceNavigation({
  schema,
  activeStep,
  onSelect,
}: WorkspaceNavigationProps) {
  return (
    <Paper component="nav" className="structure-navigation">
      <Typography variant="subtitle2">引导步骤</Typography>
      <List dense disablePadding>
        <NavigationItem
          id="packstudio_summary"
          label="概要"
          activeStep={activeStep}
          onSelect={onSelect}
        />
        {schema.steps.filter((step) => step.id !== 'modeling').map((step) => (
          <Fragment key={step.id}>
            <NavigationItem
              id={step.id}
              label={step.label}
              activeStep={activeStep}
              onSelect={onSelect}
            />
            {step.id === 'thermal_vias' && schema.template_id !== 'chip_array' && (
              <NavigationItem id="packstudio_via_removal" label="热通孔去除"
                activeStep={activeStep} onSelect={onSelect} />
            )}
            {schema.has_bga && step.id === 'solder_balls' && (
              <>
                <NavigationItem
                  id="packstudio_bga_removal"
                  label="焊球去除"
                  activeStep={activeStep}
                  onSelect={onSelect}
                />
                <NavigationItem
                  id="packstudio_bga_center"
                  label="中央焊球"
                  activeStep={activeStep}
                  onSelect={onSelect}
                />
              </>
            )}
          </Fragment>
        ))}
        {(schema.has_bga || schema.steps.some((step) => step.id === 'modeling')) && (
          <NavigationItem
            id="packstudio_modeling"
            label="建模选项"
            activeStep={activeStep}
            onSelect={onSelect}
          />
        )}
      </List>
    </Paper>
  )
}

function NavigationItem({
  id,
  label,
  activeStep,
  onSelect,
}: {
  id: string
  label: string
  activeStep: string
  onSelect: (stepId: string) => void
}) {
  return (
    <ListItemButton selected={activeStep === id} onClick={() => onSelect(id)}>
      <ListItemText primary={label} />
    </ListItemButton>
  )
}
