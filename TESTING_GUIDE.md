# 🧪 Testing Guide - Enhanced Admin Dashboard

## 🚀 Quick Start Testing

### Prerequisites
1. **Firebase Setup**: Ensure Firebase project is configured with Firestore enabled
2. **Development Server**: Run `npm start` to start the development server
3. **Admin Account**: Create an admin account using the sign-up feature

## 📋 Feature Testing Checklist

### 1. ✅ API Keys Management
**Navigate to**: API Keys tab

**Test Steps**:
1. Enter API keys for all four services (OpenAI, Apollo, Apifi, Perplexity)
2. Test show/hide password functionality
3. Verify key masking in UI after saving
4. Save and reload page to confirm persistence
5. Check security notice display

**Expected Results**:
- Keys are masked when hidden
- Keys persist after page reload
- Visual confirmation of configured keys
- Secure storage in Firebase

### 2. ✅ Project Creation & Management
**Navigate to**: Projects tab

**Test Steps**:
1. Click "New Project" button
2. Fill out project creation form:
   - **Name**: "Test Outreach Campaign"
   - **Area Description**: "Downtown San Francisco, 94105, Tech Startups"
   - **Project Details**: Add detailed description (test character counter)
   - **Email Considerations**: Add email guidelines (test 300 char limit)
   - **Follow-up Considerations**: Add follow-up strategy (test 300 char limit)
3. Create project and verify it appears in project list
4. Click on project to select it

**Expected Results**:
- Form validation works correctly
- Character counters update in real-time
- Project appears in grid layout
- Project selection highlights the card

### 3. ✅ Enhanced Lead Management
**Navigate to**: Leads tab (after selecting a project)

**Test Steps**:
1. Verify "No project selected" message when no project is chosen
2. Select a project and verify leads interface loads
3. Click "Add Lead" and fill out form:
   - **Email**: test@example.com (test validation)
   - **Name**: John Doe
   - **Company**: Acme Corp
   - **Source**: LinkedIn
   - **Notes**: Test lead for campaign
4. Add multiple leads to test table functionality
5. Test "Simple View" vs "Detailed View" toggle
6. Test column sorting by clicking headers
7. Test CSV export functionality

**Expected Results**:
- Lead addition works with validation
- Table displays all lead information
- View toggle changes visible columns
- Sorting works with visual indicators
- CSV export downloads with proper filename

### 4. ✅ Table Features Testing
**In the Enhanced Leads table**:

**Test Steps**:
1. Add several leads with different data
2. Click column headers to test sorting:
   - Email (alphabetical)
   - Status (by status type)
   - Created date (chronological)
3. Toggle between Simple and Detailed views
4. Test responsive design by resizing window
5. Hover over rows to see hover effects

**Expected Results**:
- Sorting works in both directions (asc/desc)
- Visual sort indicators appear
- Responsive design maintains usability
- Hover effects provide good UX

### 5. ✅ CSV Export Testing
**In the Enhanced Leads section**:

**Test Steps**:
1. Add multiple leads with varied data
2. Click "Export CSV" button
3. Open downloaded file
4. Verify all data fields are present and properly formatted

**Expected Results**:
- File downloads with project name and date
- All lead fields are included
- CSV format is properly quoted
- Data matches what's displayed in table

### 6. ✅ Project-Scoped Operations
**Test across multiple projects**:

**Test Steps**:
1. Create 2-3 different projects
2. Add leads to each project
3. Switch between projects
4. Verify leads are project-specific
5. Test blacklisting in one project doesn't affect others

**Expected Results**:
- Leads are isolated per project
- Project switching works smoothly
- Lead counts update correctly
- Project-specific blacklisting works

### 7. ✅ Navigation & UX Testing
**Test overall user experience**:

**Test Steps**:
1. Navigate through all tabs
2. Test project selection flow (should auto-switch to leads)
3. Verify loading states appear during operations
4. Test error handling with invalid data
5. Check toast notifications for all actions

**Expected Results**:
- Smooth navigation between sections
- Automatic tab switching works
- Loading states provide feedback
- Error messages are helpful
- Success notifications confirm actions

## 🐛 Common Issues & Solutions

### Build Issues
- **"Unexpected end of JSON input"**: Firebase config issue, use development mode
- **TypeScript errors**: All should be resolved in current implementation

### Runtime Issues
- **Firestore permissions**: Ensure authentication is enabled
- **Missing data**: Check Firebase console for proper collection creation
- **API key storage**: Verify Firestore security rules allow authenticated writes

## 🎯 Success Criteria

### All Features Working ✅
- [ ] API keys can be saved and retrieved
- [ ] Projects can be created with all required fields
- [ ] Leads can be added to projects
- [ ] CSV export works with proper data
- [ ] Table sorting and views function correctly
- [ ] Project-scoped operations work as expected
- [ ] Navigation and UX are smooth and responsive

### Performance ✅
- [ ] Page loads quickly
- [ ] Operations complete without delays
- [ ] No console errors
- [ ] Responsive design works on different screen sizes

### Data Integrity ✅
- [ ] All data persists correctly in Firebase
- [ ] Project-lead relationships are maintained
- [ ] Character limits are enforced
- [ ] Email validation works properly

## 🚀 Ready for Production!

Once all tests pass, the enhanced admin dashboard is ready for production deployment with all the ambitious features implemented perfectly! 🎉 