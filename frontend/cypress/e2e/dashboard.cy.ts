describe('Dashboard', () => {
  beforeEach(() => {
    cy.visit('/')
  })

  it('should display the dashboard title', () => {
    cy.contains('Dashboard').should('be.visible')
  })

  it('should have navigation links', () => {
    cy.contains('Requirements').should('be.visible')
    cy.contains('Code Checklist').should('be.visible')
    cy.contains('Planning').should('be.visible')
    cy.contains('Prompts').should('be.visible')
    cy.contains('Audit').should('be.visible')
  })

  it('should navigate to requirements page', () => {
    cy.contains('Requirements').click()
    cy.url().should('include', '/requirements')
  })
})
