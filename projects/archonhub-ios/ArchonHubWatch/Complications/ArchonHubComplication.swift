import ClockKit

final class ArchonHubComplication: NSObject, CLKComplicationDataSource {
    func getComplicationDescriptors(handler: @escaping ([CLKComplicationDescriptor]) -> Void) {
        let descriptor = CLKComplicationDescriptor(
            identifier: "archonhub.complication",
            displayName: "ArchonHub",
            supportedFamilies: supportedFamilies()
        )
        handler([descriptor])
    }

    func handleSharedComplicationDescriptors(_ complicationDescriptors: [CLKComplicationDescriptor]) { }

    func getSupportedTimeTravelDirections(for complication: CLKComplication, withHandler handler: @escaping (CLKComplicationTimeTravelDirections) -> Void) {
        handler([])
    }

    func getCurrentTimelineEntry(for complication: CLKComplication, withHandler handler: @escaping (CLKComplicationTimelineEntry?) -> Void) {
        handler(
            CLKComplicationTimelineEntry(date: .now, complicationTemplate: template(for: complication.family))
        )
    }

    func getTimelineStartDate(for complication: CLKComplication, withHandler handler: @escaping (Date?) -> Void) {
        handler(.now)
    }

    func getTimelineEndDate(for complication: CLKComplication, withHandler handler: @escaping (Date?) -> Void) {
        handler(.now.addingTimeInterval(60 * 30))
    }

    func getPrivacyBehavior(for complication: CLKComplication, withHandler handler: @escaping (CLKComplicationPrivacyBehavior) -> Void) {
        handler(.showOnLockScreen)
    }

    func getLocalizableSampleTemplate(for complication: CLKComplication, withHandler handler: @escaping (CLKComplicationTemplate?) -> Void) {
        handler(template(for: complication.family))
    }

    private func supportedFamilies() -> [CLKComplicationFamily] {
        [.circularSmall, .modularSmall, .utilitarianSmall, .graphicCircular]
    }

    private func template(for family: CLKComplicationFamily) -> CLKComplicationTemplate? {
        let activeRuns = UserDefaults.standard.integer(forKey: "archonhub.complication.activeRuns")
        let pendingTodos = UserDefaults.standard.integer(forKey: "archonhub.complication.pendingTodos")
        let summary = activeRuns > 0 ? "\(activeRuns) Runs" : "\(pendingTodos) Todos"

        switch family {
        case .circularSmall:
            return CLKComplicationTemplateCircularSmallSimpleText(
                textProvider: CLKSimpleTextProvider(text: "\(activeRuns)")
            )
        case .modularSmall:
            return CLKComplicationTemplateModularSmallStackText(
                line1TextProvider: CLKSimpleTextProvider(text: "Archon"),
                line2TextProvider: CLKSimpleTextProvider(text: summary)
            )
        case .utilitarianSmall:
            return CLKComplicationTemplateUtilitarianSmallFlat(
                textProvider: CLKSimpleTextProvider(text: summary)
            )
        case .graphicCircular:
            return CLKComplicationTemplateGraphicCircularStackText(
                line1TextProvider: CLKSimpleTextProvider(text: "Hub"),
                line2TextProvider: CLKSimpleTextProvider(text: "\(activeRuns)")
            )
        default:
            return nil
        }
    }
}
