const Dashboard = () => {
  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Dashboard</h1>
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Welcome to AI Agent Builder</h2>
        <p className="text-gray-600 mb-4">
          This is your project dashboard. From here you can manage your AI agent projects,
          requirements, and monitor the building process.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="font-semibold text-blue-900">Projects</h3>
            <p className="text-2xl font-bold text-blue-600">0</p>
          </div>
          <div className="bg-green-50 p-4 rounded-lg">
            <h3 className="font-semibold text-green-900">Completed</h3>
            <p className="text-2xl font-bold text-green-600">0</p>
          </div>
          <div className="bg-yellow-50 p-4 rounded-lg">
            <h3 className="font-semibold text-yellow-900">In Progress</h3>
            <p className="text-2xl font-bold text-yellow-600">0</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard